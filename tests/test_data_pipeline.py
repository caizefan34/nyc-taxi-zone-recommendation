"""Tests for the multi-year data pipeline.

Covers:
- Data configuration loading
- Download URL construction
- Raw data cleaning rules
- Temporal split correctness
- Future feature leakage prevention
- Pipeline orchestration (load → clean → split → write)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from src.data import TLCDataPipeline, compute_splits, load_pipeline_config
from src.data.download import _url, _output_path
from src.data.pipeline import DataConfig, _clean_frame


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def sample_trips() -> pl.DataFrame:
    """Synthetic trip data spanning 2022–2025 for split testing."""
    rows = []
    for year in range(2022, 2026):
        for month in range(1, 13):
            rows.append(
                {
                    "tpep_pickup_datetime": datetime(year, month, 1, 8, 0),
                    "tpep_dropoff_datetime": datetime(year, month, 1, 8, 30),
                    "PULocationID": 100,
                    "DOLocationID": 200,
                    "fare_amount": 15.0,
                    "trip_distance": 3.0,
                }
            )
    return pl.DataFrame(rows)


@pytest.fixture
def dirty_trips() -> pl.DataFrame:
    """Trip data with various quality issues for cleaning tests."""
    return pl.DataFrame(
        {
            "tpep_pickup_datetime": [
                datetime(2023, 1, 1, 8, 0),
                datetime(2023, 1, 1, 8, 0),
                datetime(2023, 1, 1, 8, 0),
                datetime(2023, 1, 1, 8, 0),
                datetime(2023, 1, 1, 8, 0),
                datetime(2023, 1, 1, 8, 0),
            ],
            "tpep_dropoff_datetime": [
                datetime(2023, 1, 1, 8, 30),  # ok
                datetime(2023, 1, 1, 7, 30),  # pickup after dropoff
                datetime(2023, 1, 1, 8, 35),  # ok
                datetime(2023, 1, 1, 8, 30),  # ok
                datetime(2023, 1, 1, 8, 30),  # ok
                datetime(2023, 1, 1, 12, 0),  # duration > 240 min
            ],
            "PULocationID": [100, 100, 0, 300, 100, 100],
            "DOLocationID": [200, 200, 200, 200, 0, 200],
            "fare_amount": [15.0, 15.0, 15.0, 15.0, 15.0, 15.0],
            "trip_distance": [3.0, 3.0, 3.0, 3.0, 3.0, 80.0],
        }
    )


# ===========================================================================
# Config Tests
# ===========================================================================


class TestDataConfig:
    def test_default_config_creation(self):
        config = DataConfig()
        assert config.years == (2022, 2023, 2024, 2025)
        assert config.zone_count == 263

    def test_split_boundaries_increasing(self):
        config = DataConfig()
        assert config.train_boundary == ("2022-01-01", "2024-01-01")
        assert config.val_boundary == ("2024-01-01", "2025-01-01")
        assert config.test_boundary == ("2025-01-01", "2026-01-01")

    def test_invalid_years_raises(self):
        with pytest.raises(ValueError, match="unreasonable year"):
            DataConfig(years=(1900,))

    def test_non_increasing_boundaries_raises(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            DataConfig(train_end="2025-01-01", val_end="2024-01-01")

    def test_empty_years_raises(self):
        with pytest.raises(ValueError, match="at least one year"):
            DataConfig(years=())

    def test_load_pipeline_config_from_file(self, tmp_path):
        cfg_path = tmp_path / "test_config.yaml"
        cfg_path.write_text(
            "years:\n  - 2022\n  - 2023\nraw_root: data/raw\nprocessed_root: data/processed"
        )
        config = load_pipeline_config(cfg_path)
        assert config.years == (2022, 2023)

    def test_load_pipeline_config_missing_file_uses_defaults(self):
        config = load_pipeline_config("nonexistent_config.yaml")
        assert config.years == (2022, 2023, 2024, 2025)


# ===========================================================================
# Download URL Tests
# ===========================================================================


class TestDownloadURLs:
    def test_url_format(self):
        url = _url(2023, 1)
        assert url.endswith("yellow_tripdata_2023-01.parquet")
        assert "d37ci6vzurychx" in url

    def test_url_format_december(self):
        url = _url(2022, 12)
        assert url.endswith("yellow_tripdata_2022-12.parquet")

    def test_output_path_structure(self):
        path = _output_path(Path("data/raw"), 2023, 1)
        assert path == Path("data/raw/2023/01/yellow_tripdata_2023-01.parquet")


# ===========================================================================
# Cleaning Tests
# ===========================================================================


class TestCleaning:
    def test_clean_valid_data_passes_through(self, sample_trips):
        config = DataConfig()
        cleaned = _clean_frame(sample_trips, config)
        assert cleaned.height > 0

    def test_clean_removes_invalid_zones(self, dirty_trips):
        config = DataConfig()
        cleaned = _clean_frame(dirty_trips, config)
        # Only rows with valid zones (1..263) survive zone filtering
        assert cleaned["PULocationID"].min() >= 1
        assert cleaned["DOLocationID"].max() <= 263

    def test_clean_removes_pickup_after_dropoff(self, dirty_trips):
        config = DataConfig()
        cleaned = _clean_frame(dirty_trips, config)
        assert (cleaned["tpep_pickup_datetime"] < cleaned["tpep_dropoff_datetime"]).all()

    def test_clean_enforces_duration_limit(self, dirty_trips):
        config = DataConfig(max_trip_duration_minutes=30.0)
        cleaned = _clean_frame(dirty_trips, config)
        assert cleaned["trip_duration"].max() <= 30.0

    def test_clean_enforces_fare_range(self):
        df = pl.DataFrame(
            {
                "tpep_pickup_datetime": [datetime(2023, 1, 1, 8, 0)],
                "tpep_dropoff_datetime": [datetime(2023, 1, 1, 8, 30)],
                "PULocationID": [100],
                "DOLocationID": [200],
                "fare_amount": [500.0],  # way over max
                "trip_distance": [3.0],
            }
        )
        config = DataConfig(max_fare=200.0)
        cleaned = _clean_frame(df, config)
        assert cleaned.height == 0

    def test_clean_removes_duplicates(self):
        df = pl.DataFrame(
            {
                "tpep_pickup_datetime": [datetime(2023, 1, 1, 8, 0)] * 3,
                "tpep_dropoff_datetime": [datetime(2023, 1, 1, 8, 30)] * 3,
                "PULocationID": [100] * 3,
                "DOLocationID": [200] * 3,
                "fare_amount": [15.0] * 3,
                "trip_distance": [3.0] * 3,
            }
        )
        config = DataConfig()
        cleaned = _clean_frame(df, config)
        assert cleaned.height == 1


# ===========================================================================
# Split Correctness Tests
# ===========================================================================


class TestTemporalSplit:
    def test_split_partitions_are_disjoint(self, sample_trips):
        config = DataConfig()
        splits = compute_splits(sample_trips, config=config)
        ids_train = set(splits["train"]["tpep_pickup_datetime"].to_list())
        ids_val = set(splits["validation"]["tpep_pickup_datetime"].to_list())
        ids_test = set(splits["test"]["tpep_pickup_datetime"].to_list())
        # No overlap between any pair
        assert ids_train.isdisjoint(ids_val)
        assert ids_train.isdisjoint(ids_test)
        assert ids_val.isdisjoint(ids_test)

    def test_split_time_ordering(self, sample_trips):
        """Train data must be strictly before validation, validation before test."""
        config = DataConfig()
        splits = compute_splits(sample_trips, config=config)

        if splits["train"].height > 0:
            assert splits["train"]["tpep_pickup_datetime"].max() < datetime(2024, 1, 1)
        if splits["validation"].height > 0:
            assert splits["validation"]["tpep_pickup_datetime"].min() >= datetime(2024, 1, 1)
            val_max = splits["validation"]["tpep_pickup_datetime"].max()
            if val_max is not None:
                assert val_max < datetime(2025, 1, 1)
        if splits["test"].height > 0:
            assert splits["test"]["tpep_pickup_datetime"].min() >= datetime(2025, 1, 1)

    def test_split_all_data_preserved(self, sample_trips):
        """Union of all splits should equal the original data."""
        config = DataConfig()
        splits = compute_splits(sample_trips, config=config)
        total = sum(s.height for s in splits.values())
        assert total == sample_trips.height

    def test_no_future_features_in_train(self, sample_trips):
        """Train split must contain no 2024 or 2025 data."""
        config = DataConfig()
        splits = compute_splits(sample_trips, config=config)
        if splits["train"].height > 0:
            max_year = splits["train"]["tpep_pickup_datetime"].dt.year().max()
            assert max_year < 2024, f"Train contains data from {max_year}"

    def test_validation_has_no_test_data(self, sample_trips):
        """Validation must not contain 2025 data."""
        config = DataConfig()
        splits = compute_splits(sample_trips, config=config)
        if splits["validation"].height > 0:
            max_year = splits["validation"]["tpep_pickup_datetime"].dt.year().max()
            assert max_year < 2025, f"Validation contains data from {max_year}"


# ===========================================================================
# Pipeline Orchestration Tests
# ===========================================================================


class TestPipeline:
    def test_list_raw_files_empty(self, tmp_path):
        config = DataConfig(raw_root=str(tmp_path), years=(2023,))
        pipeline = TLCDataPipeline(config)
        files = pipeline.list_raw_files()
        assert files == []

    def test_list_raw_files_finds_existing(self, tmp_path):
        # Create a fake raw file
        out_dir = tmp_path / "2023" / "01"
        out_dir.mkdir(parents=True, exist_ok=True)
        dummy = out_dir / "yellow_tripdata_2023-01.parquet"
        dummy.write_text("fake data")

        config = DataConfig(raw_root=str(tmp_path), years=(2023,))
        pipeline = TLCDataPipeline(config)
        files = pipeline.list_raw_files()
        assert len(files) == 1

    def test_pipeline_load_and_clean_without_data_raises(self, tmp_path):
        config = DataConfig(raw_root=str(tmp_path), years=(2023,))
        pipeline = TLCDataPipeline(config)
        with pytest.raises(FileNotFoundError, match="No raw parquet files"):
            pipeline.load_and_clean()

    def test_write_splits_creates_output(self, sample_trips, tmp_path):
        config = DataConfig(
            raw_root=str(tmp_path),
            processed_root=str(tmp_path / "out"),
            years=(2022, 2023, 2024, 2025),
        )
        splits = compute_splits(sample_trips, config=config)
        pipeline = TLCDataPipeline(config)
        outputs = pipeline.write_splits(splits)
        assert "train" in outputs
        assert "validation" in outputs
        assert "test" in outputs
        for path in outputs.values():
            assert Path(path).exists()

    def test_write_splits_creates_manifest(self, sample_trips, tmp_path):
        config = DataConfig(
            raw_root=str(tmp_path),
            processed_root=str(tmp_path / "out"),
        )
        splits = compute_splits(sample_trips, config=config)
        pipeline = TLCDataPipeline(config)
        pipeline.write_splits(splits)
        manifest = tmp_path / "out" / "splits.json"
        assert manifest.exists()
        assert "train" in manifest.read_text()

"""Multi-year TLC data pipeline with strict temporal split.

Processes raw TLC parquet files into cleaned, time-partitioned datasets
using Polars for efficient large-scale columnar processing.

Split strategy (strict time isolation):
  - Train:      2022-01-01 00:00:00  to  2023-12-31 23:59:59
  - Validation: 2024-01-01 00:00:00  to  2024-12-31 23:59:59
  - Test:       2025-01-01 00:00:00  to  2025-12-31 23:59:59
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence

import polars as pl

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DataConfig:
    """Pipeline configuration loaded from ``data/config.yaml``."""

    years: tuple[int, ...] = (2022, 2023, 2024, 2025)
    raw_root: str = "data/raw"
    processed_root: str = "data/processed/multi_year"
    zone_count: int = 263

    # Cleaning thresholds (same as src/1_data_clean/clean.py)
    max_trip_duration_minutes: float = 240.0
    min_trip_duration_minutes: float = 1.0
    max_fare: float = 200.0
    min_fare: float = 0.0
    max_trip_distance: float = 100.0
    min_trip_distance: float = 0.1
    max_speed_mph: float = 80.0

    # Temporal split boundaries
    train_end: str = "2024-01-01"
    val_end: str = "2025-01-01"
    test_end: str = "2026-01-01"

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not self.years:
            raise ValueError("at least one year is required")
        for y in self.years:
            if y < 2009 or y > 2026:
                raise ValueError(f"unreasonable year: {y}")
        train_dt = datetime.fromisoformat(self.train_end)
        val_dt = datetime.fromisoformat(self.val_end)
        test_dt = datetime.fromisoformat(self.test_end)
        if not (train_dt < val_dt < test_dt):
            raise ValueError("split boundaries must be strictly increasing")

    @property
    def train_boundary(self) -> tuple[str, str]:
        return (f"{min(self.years)}-01-01", self.train_end)

    @property
    def val_boundary(self) -> tuple[str, str]:
        return (self.train_end, self.val_end)

    @property
    def test_boundary(self) -> tuple[str, str]:
        return (self.val_end, self.test_end)


def load_pipeline_config(path: str | Path = "data/config.yaml") -> DataConfig:
    """Load pipeline config from YAML or return defaults.

    Args:
        path: Path to YAML config file. If the file does not exist,
            returns default ``DataConfig``.

    Returns:
        Populated ``DataConfig`` instance.
    """
    p = Path(path)
    if not p.exists():
        logger.warning("Pipeline config %s not found; using defaults", p)
        return DataConfig()

    import yaml

    with open(p, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return DataConfig()

    return DataConfig(
        years=tuple(raw.get("years", DataConfig.years)),
        raw_root=raw.get("raw_root", DataConfig.raw_root),
        processed_root=raw.get("processed_root", DataConfig.processed_root),
        zone_count=raw.get("zone_count", DataConfig.zone_count),
        max_trip_duration_minutes=raw.get(
            "max_trip_duration_minutes", DataConfig.max_trip_duration_minutes
        ),
        min_trip_duration_minutes=raw.get(
            "min_trip_duration_minutes", DataConfig.min_trip_duration_minutes
        ),
        max_fare=raw.get("max_fare", DataConfig.max_fare),
        min_fare=raw.get("min_fare", DataConfig.min_fare),
        max_trip_distance=raw.get("max_trip_distance", DataConfig.max_trip_distance),
        min_trip_distance=raw.get("min_trip_distance", DataConfig.min_trip_distance),
        max_speed_mph=raw.get("max_speed_mph", DataConfig.max_speed_mph),
        train_end=raw.get("train_end", DataConfig.train_end),
        val_end=raw.get("val_end", DataConfig.val_end),
        test_end=raw.get("test_end", DataConfig.test_end),
    )


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

_REQUIRED_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "trip_distance",
]

_SCHEMA_OVERWRITE = {
    "PULocationID": pl.Int32,
    "DOLocationID": pl.Int32,
    "fare_amount": pl.Float64,
    "trip_distance": pl.Float64,
}


def _read_parquet(path: Path) -> pl.DataFrame:
    """Read a parquet file, casting known columns for consistency."""
    return pl.scan_parquet(str(path)).collect()


def _clean_frame(df: pl.DataFrame, config: DataConfig) -> pl.DataFrame:
    """Apply cleaning rules to a single DataFrame.

    Rules mirror those in ``src/1_data_clean/clean.py``.
    """
    required = [c for c in _REQUIRED_COLUMNS if c in df.columns]
    if len(required) < 4:
        raise ValueError(f"too few required columns available: {required}")

    # Cast zone IDs
    df = df.with_columns(
        pl.col("PULocationID").cast(pl.Int32),
        pl.col("DOLocationID").cast(pl.Int32),
    )

    # Ensure datetime columns are datetime type (handle both string and datetime inputs)
    for col_name in ("tpep_pickup_datetime", "tpep_dropoff_datetime"):
        if df.schema[col_name] == pl.String:
            df = df.with_columns(
                pl.col(col_name).str.to_datetime(time_zone=None).alias(col_name)
            )
        elif df.schema[col_name] != pl.Datetime:
            df = df.with_columns(
                pl.col(col_name).cast(pl.Datetime).alias(col_name)
            )

    # Temporal consistency
    df = df.filter(
        pl.col("tpep_pickup_datetime") < pl.col("tpep_dropoff_datetime")
    )

    # Valid zone IDs
    df = df.filter(
        pl.col("PULocationID").is_between(1, config.zone_count),
        pl.col("DOLocationID").is_between(1, config.zone_count),
    )

    # Fare range
    if "fare_amount" in df.columns:
        df = df.with_columns(pl.col("fare_amount").cast(pl.Float64))
        df = df.filter(
            pl.col("fare_amount").is_between(config.min_fare, config.max_fare)
        )

    # Trip duration
    df = df.with_columns(
        ((pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime"))
         .dt.total_milliseconds() / 60000.0).alias("trip_duration")
    )
    df = df.filter(
        pl.col("trip_duration").is_between(
            config.min_trip_duration_minutes, config.max_trip_duration_minutes
        )
    )

    # Trip distance
    if "trip_distance" in df.columns:
        df = df.with_columns(pl.col("trip_distance").cast(pl.Float64))
        df = df.filter(
            pl.col("trip_distance").is_between(
                config.min_trip_distance, config.max_trip_distance
            )
        )
        # Speed cap
        speed = pl.col("trip_distance") / (pl.col("trip_duration") / 60.0)
        df = df.filter(speed <= config.max_speed_mph)

    # Drop duplicates
    dedup_cols = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
    ]
    df = df.unique(subset=[c for c in dedup_cols if c in df.columns])

    return df


# ---------------------------------------------------------------------------
# Temporal split
# ---------------------------------------------------------------------------

# Split boundary constants used internally
_SPLIT_LABELS = ("train", "validation", "test")


def compute_splits(
    df: pl.DataFrame,
    *,
    config: DataConfig,
) -> dict[str, pl.DataFrame]:
    """Split a full-year DataFrame into train/validation/test partitions.

    All partition decisions are based solely on ``tpep_pickup_datetime``,
    ensuring strict temporal isolation with no future information leakage.

    Returns:
        Dictionary with keys ``"train"``, ``"validation"``, ``"test"``.
    """
    train_start, train_end = config.train_boundary
    val_start, val_end = config.val_boundary
    test_start, test_end = config.test_boundary

    train = df.filter(
        pl.col("tpep_pickup_datetime").is_between(
            datetime.fromisoformat(train_start), datetime.fromisoformat(train_end)
        )
    )
    validation = df.filter(
        pl.col("tpep_pickup_datetime").is_between(
            datetime.fromisoformat(val_start), datetime.fromisoformat(val_end)
        )
    )
    test = df.filter(
        pl.col("tpep_pickup_datetime").is_between(
            datetime.fromisoformat(test_start), datetime.fromisoformat(test_end)
        )
    )

    return {"train": train, "validation": validation, "test": test}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class TLCDataPipeline:
    """End-to-end multi-year TLC data pipeline.

    Orchestrates reading raw parquet files, cleaning, and writing
    time-partitioned outputs.
    """

    def __init__(self, config: DataConfig | None = None) -> None:
        self.config = config or DataConfig()

    @property
    def raw_root(self) -> Path:
        return Path(self.config.raw_root)

    @property
    def processed_root(self) -> Path:
        return Path(self.config.processed_root)

    def list_raw_files(self) -> list[Path]:
        """Discover all raw parquet files for configured years."""
        files: list[Path] = []
        for year in self.config.years:
            for month in range(1, 13):
                p = self.raw_root / str(year) / f"{month:02d}" / f"yellow_tripdata_{year}-{month:02d}.parquet"
                if p.exists():
                    files.append(p)
        return files

    def load_and_clean(self, *, progress: bool = False) -> dict[str, pl.DataFrame]:
        """Read all raw files, clean, and split into train/validation/test.

        Args:
            progress: If True, log progress per file.

        Returns:
            Dictionary with keys ``"train"``, ``"validation"``, ``"test"``.
        """
        files = self.list_raw_files()
        if not files:
            raise FileNotFoundError(
                f"No raw parquet files found under {self.raw_root} for years {self.config.years}. "
                "Run `python -m src.data.download_range` first."
            )

        partitions: dict[str, pl.DataFrame] = {}
        for label in _SPLIT_LABELS:
            partitions[label] = pl.DataFrame()

        for file in sorted(files):
            if progress:
                logger.info("Processing %s", file)

            df = _read_parquet(file)
            df = _clean_frame(df, self.config)
            split = compute_splits(df, config=self.config)

            for label in _SPLIT_LABELS:
                if split[label].height > 0:
                    partitions[label] = pl.concat([partitions[label], split[label]], how="vertical")

        for label in _SPLIT_LABELS:
            if partitions[label].height > 0:
                partitions[label] = partitions[label].unique(
                    subset=[c for c in _REQUIRED_COLUMNS if c in partitions[label].columns]
                )

        return partitions

    def write_splits(self, partitions: dict[str, pl.DataFrame]) -> dict[str, Path]:
        """Write each partition to its output directory as parquet.

        Each partition is written as a single parquet file for efficient
        downstream loading.

        Returns:
            Dictionary mapping split label to output path.
        """
        outputs: dict[str, Path] = {}
        for label in _SPLIT_LABELS:
            df = partitions[label]
            if df.height == 0:
                continue
            out_dir = self.processed_root / label
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "data.parquet"
            df.write_parquet(str(path), compression="zstd")
            outputs[label] = path
            logger.info("Wrote %s: %s rows → %s", label, f"{df.height:,}", path)

        self._write_split_manifest(partitions)
        return outputs

    def _write_split_manifest(self, partitions: dict[str, pl.DataFrame]) -> Path:
        """Write a JSON manifest describing the split."""
        manifest = {
            "config": {
                "train_end": self.config.train_end,
                "val_end": self.config.val_end,
                "test_end": self.config.test_end,
            },
            "years": list(self.config.years),
            "splits": {},
        }
        for label in _SPLIT_LABELS:
            df = partitions[label]
            manifest["splits"][label] = {
                "rows": df.height,
                "columns": list(df.columns) if df.height > 0 else [],
            }
            if df.height > 0:
                manifest["splits"][label]["time_range"] = [
                    str(df["tpep_pickup_datetime"].min()),
                    str(df["tpep_pickup_datetime"].max()),
                ]

        out_path = self.processed_root / "splits.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        logger.info("Manifest written to %s", out_path)
        return out_path

    def run(self, *, progress: bool = True) -> dict[str, Path]:
        """Execute the full pipeline: load → clean → split → write.

        Args:
            progress: If True, log progress per file.

        Returns:
            Dictionary mapping split label to output path.
        """
        partitions = self.load_and_clean(progress=progress)
        return self.write_splits(partitions)


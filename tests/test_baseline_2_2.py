"""Tests for Baseline 2 strategy."""
import importlib.util
from datetime import datetime
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
requires_data = pytest.mark.skipif(
    not (DATA_DIR / "zone_time_statistics.parquet").exists(),
    reason="Data files not available"
)

try:
    spec = importlib.util.spec_from_file_location(
        "baseline_2_2",
        Path(__file__).resolve().parents[1] / "src" / "2_recommendation_algorithm" / "baseline_2_2.py"
    )
    baseline_2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline_2)
    HAS_DATA = True
except (FileNotFoundError, OSError):
    HAS_DATA = False


class TestBaseline2:
    """Tests for Baseline 2 strategy."""

    @requires_data
    def test_recommend_returns_list(self, sample_datetime, sample_location_id):
        result = baseline_2.recommend(sample_datetime, sample_location_id)
        assert isinstance(result, list)
        assert len(result) == 3

    @requires_data
    def test_recommend_valid_ids(self, sample_datetime, sample_location_id):
        result = baseline_2.recommend(sample_datetime, sample_location_id)
        for z in result:
            assert 1 <= z <= 263

    @requires_data
    def test_recommend_unique(self, sample_datetime, sample_location_id):
        result = baseline_2.recommend(sample_datetime, sample_location_id)
        assert len(set(result)) == 3

    @requires_data
    def test_invalid_inputs(self):
        with pytest.raises(ValueError):
            baseline_2.recommend(datetime(2023, 1, 15, 8, 0), 0)
        with pytest.raises(ValueError):
            baseline_2.recommend(datetime(2023, 1, 15, 8, 0), 264)
        with pytest.raises(TypeError):
            baseline_2.recommend("invalid", 1)

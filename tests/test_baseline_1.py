"""Tests for Baseline 1 strategy."""
import importlib.util
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
requires_data = pytest.mark.skipif(
    not (DATA_DIR / "zone_time_statistics.parquet").exists(),
    reason="Data files not available - download from NYC TLC"
)

try:
    spec = importlib.util.spec_from_file_location(
        "baseline_1",
        Path(__file__).resolve().parents[1] / "src" / "2_recommendation_algorithm" / "baseline_1.py"
    )
    baseline_1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline_1)
    HAS_DATA = True
except (FileNotFoundError, OSError):
    HAS_DATA = False


class TestBaseline1:
    """Tests for Baseline 1 strategy."""

    @requires_data
    def test_recommend_returns_list(self, sample_datetime, sample_location_id):
        result = baseline_1.recommend(sample_datetime, sample_location_id)
        assert isinstance(result, list)

    @requires_data
    def test_recommend_returns_three_zones(self, sample_datetime, sample_location_id):
        result = baseline_1.recommend(sample_datetime, sample_location_id)
        assert len(result) == 3

    @requires_data
    def test_recommend_valid_zone_ids(self, sample_datetime, sample_location_id):
        result = baseline_1.recommend(sample_datetime, sample_location_id)
        for zone in result:
            assert 1 <= zone <= 263

    @requires_data
    def test_recommend_unique_zones(self, sample_datetime, sample_location_id):
        result = baseline_1.recommend(sample_datetime, sample_location_id)
        assert len(set(result)) == 3

    @requires_data
    def test_invalid_location_raises_error(self, sample_datetime):
        with pytest.raises(ValueError):
            baseline_1.recommend(sample_datetime, 0)
        with pytest.raises(ValueError):
            baseline_1.recommend(sample_datetime, 264)

    @requires_data
    def test_invalid_datetime_raises_error(self, sample_location_id):
        with pytest.raises(TypeError):
            baseline_1.recommend("not a datetime", sample_location_id)

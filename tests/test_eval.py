"""Tests for evaluation core functions (mock-based)."""
import pytest
from datetime import datetime


def validate_top3(prediction):
    """Simplified validate_top3 for testing purposes."""
    pred = tuple(prediction)
    if len(pred) != 3:
        raise ValueError("prediction must contain exactly 3 zones")
    if len(set(pred)) != 3:
        raise ValueError("prediction zones must be unique")
    for z in pred:
        if not (1 <= z <= 263):
            raise ValueError(f"zone {z} is out of 1..263 range")
    return pred


class TestValidateTop3:
    """Tests for the validate_top3 function."""

    def test_valid_tuple(self):
        pred = validate_top3((1, 2, 3))
        assert pred == (1, 2, 3)

    def test_valid_list(self):
        pred = validate_top3([1, 2, 3])
        assert pred == (1, 2, 3)

    def test_duplicates_raises_error(self):
        with pytest.raises(ValueError, match="unique"):
            validate_top3((1, 1, 2))

    def test_out_of_range_low(self):
        with pytest.raises(ValueError, match="0 is out of"):
            validate_top3((0, 1, 2))

    def test_out_of_range_high(self):
        with pytest.raises(ValueError, match="264 is out of"):
            validate_top3((1, 2, 264))

    def test_wrong_length_short(self):
        with pytest.raises(ValueError, match="exactly 3"):
            validate_top3((1, 2))

    def test_wrong_length_long(self):
        with pytest.raises(ValueError, match="exactly 3"):
            validate_top3((1, 2, 3, 4))


class TestQueryStructure:
    """Tests for query data structure."""

    def test_query_has_required_fields(self):
        q = {"query_id": 1, "current_location_id": 132, "query_time": datetime(2023, 1, 15, 8, 0)}
        assert q["query_id"] == 1
        assert q["current_location_id"] == 132
        assert q["query_time"].hour == 8
        assert q["query_time"].weekday() == 6  # Sunday
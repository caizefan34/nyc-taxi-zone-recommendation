"""Tests for the improved two-step planning strategy."""
import importlib.util
from pathlib import Path
from datetime import datetime
import unittest

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
requires_data = pytest.mark.skipif(
    not (DATA_DIR / "zone_time_statistics.parquet").exists(),
    reason="Data files not available"
)

try:
    spec = importlib.util.spec_from_file_location(
        "improved_strategy",
        Path(__file__).resolve().parents[1] / "src" / "2_recommendation_algorithm" / "improved_strategy.py"
    )
    strategy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy)
    HAS_DATA = True
except (FileNotFoundError, OSError):
    HAS_DATA = False


class TestImprovedStrategy(unittest.TestCase):
    """Comprehensive tests for improved_strategy.recommend()."""

    @requires_data
    def test_recommend_returns_list_of_ints(self):
        result = strategy.recommend(datetime(2023, 1, 15, 8, 0), 132)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    @requires_data
    def test_recommend_valid_range(self):
        result = strategy.recommend(datetime(2023, 1, 15, 8, 0), 132)
        for z in result:
            self.assertGreaterEqual(z, 1)
            self.assertLessEqual(z, 263)

    @requires_data
    def test_recommend_unique_zones(self):
        result = strategy.recommend(datetime(2023, 1, 15, 8, 0), 132)
        self.assertEqual(len(set(result)), 3)

    @requires_data
    def test_edge_cases(self):
        r1 = strategy.recommend(datetime(2023, 1, 15, 23, 45), 132)
        self.assertEqual(len(r1), 3)
        r2 = strategy.recommend(datetime(2023, 1, 25, 0, 0), 1)
        self.assertEqual(len(r2), 3)

    @requires_data
    def test_raises_errors(self):
        with self.assertRaises(TypeError):
            strategy.recommend("not-a-datetime", 132)
        with self.assertRaises(ValueError):
            strategy.recommend(datetime(2023, 1, 15, 8, 0), 0)
        with self.assertRaises(ValueError):
            strategy.recommend(datetime(2023, 1, 15, 8, 0), 264)

if __name__ == "__main__":
    unittest.main()
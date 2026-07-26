"""Tests for forecast evaluation metrics (SMAPE, masked MAPE)."""
from __future__ import annotations

import numpy as np

from src.forecasting.evaluation import _masked_mape, _smape


class TestSMAPE:
    def test_perfect_prediction(self):
        a = np.array([10.0, 20.0, 30.0])
        assert _smape(a, a) < 1e-6

    def test_bounded_by_200(self):
        a = np.array([10.0])
        b = np.array([0.0])
        result = _smape(a, b)
        assert result <= 200.0
        assert result >= 0.0

    def test_zero_denom_handling(self):
        a = np.array([0.0, 0.0])
        b = np.array([0.0, 0.0])
        assert _smape(a, b) == 0.0

    def test_finite_output(self):
        rng = np.random.default_rng(42)
        a = rng.exponential(10.0, 100)
        b = a * (0.9 + 0.2 * rng.random(100))
        assert np.isfinite(_smape(a, b))


class TestMaskedMAPE:
    def test_perfect_prediction(self):
        a = np.array([10.0, 20.0, 30.0])
        assert _masked_mape(a, a) < 1e-6

    def test_masks_near_zero(self):
        a = np.array([0.0, 0.0, 10.0])
        b = np.array([5.0, 5.0, 12.0])
        result = _masked_mape(a, b)
        assert np.isfinite(result)
        assert result > 0.0

    def test_threshold_filtering(self):
        a = np.array([0.5, 1.0, 10.0])
        b = np.array([0.0, 0.0, 12.0])
        low_thresh = _masked_mape(a, b, threshold=0.1)
        high_thresh = _masked_mape(a, b, threshold=5.0)
        assert low_thresh != high_thresh

    def test_all_below_threshold(self):
        a = np.array([0.1, 0.2, 0.3])
        b = np.array([0.0, 0.0, 0.0])
        assert _masked_mape(a, b, threshold=1.0) == 0.0

    def test_finite_output(self):
        rng = np.random.default_rng(42)
        a = rng.exponential(10.0, 100)
        b = a * (0.9 + 0.2 * rng.random(100))
        assert np.isfinite(_masked_mape(a, b))

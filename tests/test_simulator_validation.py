"""Tests for the simulator reality validation module.

Covers:
- Distribution comparison metrics (KL, JS, Wasserstein)
- Temporal pattern validation
- Revenue validation
"""
from __future__ import annotations

import numpy as np
import pytest

from src.simulator.validation.comparison import (
    SimulatorValidator,
    compare_distributions,
)
from src.simulator.validation.revenue import RevenueValidator
from src.simulator.validation.temporal import TemporalValidator


class TestCompareDistributions:
    def test_identical_distributions(self):
        data = np.random.rand(100)
        result = compare_distributions(data, data)
        assert result.kl_divergence < 1e-6
        assert result.js_divergence < 1e-6
        assert result.wasserstein_distance < 1e-6
        assert abs(result.correlation - 1.0) < 1e-6

    def test_different_distributions(self):
        a = np.ones(100)
        b = np.ones(100) * 2
        result = compare_distributions(a, b)
        assert result.wasserstein_distance > 0

    def test_metrics_are_finite(self):
        rng = np.random.default_rng(42)
        a = rng.exponential(1.0, 1000)
        b = rng.exponential(1.5, 1000)
        result = compare_distributions(a, b)
        assert np.isfinite(result.kl_divergence)
        assert np.isfinite(result.js_divergence)
        assert np.isfinite(result.wasserstein_distance)

    def test_large_kl_indicates_difference(self):
        a = np.random.exponential(1.0, 1000)
        b = np.random.exponential(5.0, 1000)
        result = compare_distributions(a, b)
        assert result.kl_divergence > 0.01, f"KL={result.kl_divergence} should be > 0 for different distributions"


class TestSimulatorValidator:
    @pytest.fixture
    def validator(self):
        return SimulatorValidator()

    def test_run_returns_report(self, validator):
        rng = np.random.default_rng(42)
        real_demand = rng.exponential(20.0, 263)
        sim_demand = rng.exponential(20.0, 263)
        real_hourly = rng.random(24)
        sim_hourly = rng.random(24)
        real_fares = rng.exponential(15.0, 500)
        sim_rewards = rng.exponential(15.0, 500)

        report = validator.run(real_demand, sim_demand, real_hourly, sim_hourly, real_fares, sim_rewards)
        assert report.zone_demand is not None
        assert report.hourly_pattern is not None
        assert report.revenue is not None
        assert len(report.summary) > 0

    def test_report_has_interpretation(self, validator):
        rng = np.random.default_rng(42)
        report = validator.run(
            rng.exponential(20.0, 263), rng.exponential(20.0, 263),
            rng.random(24), rng.random(24),
            rng.exponential(15.0, 500), rng.exponential(15.0, 500),
        )
        assert "zone_demand" in report.summary
        assert "hourly_pattern" in report.summary
        assert "revenue" in report.summary


class TestTemporalValidator:
    @pytest.fixture
    def validator(self):
        return TemporalValidator()

    def test_hourly_validation(self, validator):
        real = np.linspace(10, 100, 24)
        sim = np.linspace(10, 100, 24) + np.random.randn(24) * 2
        result = validator.validate_hourly(real, sim)
        assert "rmse" in result
        assert "correlation" in result
        assert result["correlation"] > 0.9

    def test_hourly_validation_wrong_size(self, validator):
        with pytest.raises(ValueError, match="length 24"):
            validator.validate_hourly(np.zeros(12), np.zeros(12))

    def test_weekday_weekend(self, validator):
        wd = np.random.rand(24)
        we = np.random.rand(24)
        result = validator.validate_weekday_weekend(wd, wd, we, we)
        assert abs(result["weekday_correlation"] - 1.0) < 1e-6
        assert abs(result["weekend_correlation"] - 1.0) < 1e-6


class TestRevenueValidator:
    @pytest.fixture
    def validator(self):
        return RevenueValidator()

    def test_identical_revenue(self, validator):
        data = np.random.exponential(15.0, 1000)
        result = validator.validate(data, data)
        assert abs(result.mean_abs_error) < 1.0
        assert result.ks_pvalue > 0.01

    def test_different_revenue(self, validator):
        a = np.random.exponential(15.0, 1000)
        b = np.random.exponential(30.0, 1000)
        result = validator.validate(a, b)
        assert result.mean_abs_error > 0

    def test_per_zone_validation(self, validator):
        zone_fares = {z: np.random.exponential(15.0, 100) for z in range(1, 11)}
        zone_rewards = {z: np.random.exponential(15.0, 100) for z in range(1, 11)}
        results = validator.validate_per_zone(zone_fares, zone_rewards)
        assert len(results) == 10

    def test_metrics_are_finite(self, validator):
        a = np.random.exponential(15.0, 500)
        b = np.random.exponential(15.0, 500)
        result = validator.validate(a, b)
        assert np.isfinite(result.real_mean)
        assert np.isfinite(result.sim_mean)
        assert np.isfinite(result.ks_statistic)
        assert np.isfinite(result.ks_pvalue)


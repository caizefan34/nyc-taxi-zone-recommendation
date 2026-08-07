"""Tests for A/B testing framework."""
from __future__ import annotations

import numpy as np

from src.evaluation.ab.testing import (
    ExperimentSource,
    PolicyMetrics,
    bootstrap_ci,
    compare_policies,
    paired_comparison,
)


class TestBootstrapCI:
    def test_normal_data(self):
        rng = np.random.RandomState(42)
        data = rng.normal(100, 10, 100).tolist()
        lo, hi = bootstrap_ci(data, n_bootstrap=500, seed=42)
        assert lo < hi
        assert 95 < lo < 105
        assert 95 < hi < 105

    def test_small_sample(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        lo, hi = bootstrap_ci(data, n_bootstrap=100, seed=42)
        assert lo < hi


class TestPairedComparison:
    def test_significant_difference(self):
        rng = np.random.RandomState(42)
        ctrl = rng.normal(100, 10, 50).tolist()
        trt = rng.normal(115, 10, 50).tolist()
        result = paired_comparison(ctrl, trt, n_bootstrap=500, seed=42)
        assert result["mean_difference"] > 0
        assert result["statistically_significant"]

    def test_no_difference(self):
        rng = np.random.RandomState(42)
        ctrl = rng.normal(100, 10, 50).tolist()
        trt = rng.normal(100, 10, 50).tolist()
        result = paired_comparison(ctrl, trt, n_bootstrap=500, seed=42)
        assert abs(result["mean_difference"]) < 5


class TestComparePolicies:
    def test_basic(self):
        rng = np.random.RandomState(42)
        control = PolicyMetrics(
            policy_name="hot_zone",
            revenue_per_vehicle=rng.normal(400, 50, 100).tolist(),
            utilization=rng.uniform(0.05, 0.15, 100).tolist(),
        )
        treatment = PolicyMetrics(
            policy_name="two_step",
            revenue_per_vehicle=rng.normal(550, 60, 100).tolist(),
            utilization=rng.uniform(0.08, 0.20, 100).tolist(),
        )
        result = compare_policies(control, treatment, source=ExperimentSource.SIMULATION)
        assert result.control_name == "hot_zone"
        assert result.treatment_name == "two_step"
        assert "revenue_per_vehicle" in result.metric_results
        assert result.source == ExperimentSource.SIMULATION

    def test_to_dict(self):
        rng = np.random.RandomState(42)
        control = PolicyMetrics(
            policy_name="a",
            revenue_per_vehicle=rng.normal(100, 10, 30).tolist(),
            utilization=rng.uniform(0.1, 0.2, 30).tolist(),
        )
        treatment = PolicyMetrics(
            policy_name="b",
            revenue_per_vehicle=rng.normal(110, 10, 30).tolist(),
            utilization=rng.uniform(0.1, 0.2, 30).tolist(),
        )
        result = compare_policies(control, treatment)
        d = result.to_dict()
        assert "source" in d
        assert "metrics" in d
        assert "note" in d


class TestPolicyMetrics:
    def test_to_dict(self):
        pm = PolicyMetrics(
            policy_name="test",
            revenue_per_vehicle=[10.0, 20.0, 30.0],
        )
        d = pm.to_dict()
        assert d["policy_name"] == "test"
        assert "revenue_per_vehicle_mean" in d

    def test_empty_metrics(self):
        pm = PolicyMetrics(policy_name="test")
        d = pm.to_dict()
        assert "revenue_per_vehicle_mean" not in d

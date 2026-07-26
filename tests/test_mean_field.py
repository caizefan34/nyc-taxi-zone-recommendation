"""Tests for Phase 6: Mean Field Game approximation.

Covers:
- MeanFieldConfig
- MeanFieldApproximation initialization/population
- Density and competition factor
- Population update
- Policy comparison evaluation
"""

from __future__ import annotations

import numpy as np
import pytest

from src.rl.mean_field import MeanFieldApproximation, MeanFieldConfig, compare_policies
from src.rl.mean_field.evaluation import PolicyComparison

# ===========================================================================
# Mean Field Tests
# ===========================================================================


class TestMeanField:
    @pytest.fixture
    def mf(self) -> MeanFieldApproximation:
        mf = MeanFieldApproximation(MeanFieldConfig(zone_count=10, total_drivers=20))
        mf.initialize()
        return mf

    def test_initialization(self, mf):
        assert mf._initialized
        assert mf.population.shape == (336, 10)
        assert abs(mf.population.sum() - 20 * 336) < 1.0

    def test_get_density(self, mf):
        density = mf.get_density(0, 1)
        assert 0 <= density <= 20
        assert np.isfinite(density)

    def test_get_distribution_shape(self, mf):
        dist = mf.get_distribution(0)
        assert dist.shape == (10,)
        assert np.all(dist >= 0)

    def test_competition_factor_bounds(self, mf):
        factor = mf.get_competition_factor(0, 1, base_demand=20.0)
        assert 0.0 <= factor <= 1.0

    def test_competition_decreases_with_density(self, mf):
        # High density should give lower prob
        high_density_pop = np.full((336, 10), 100.0)
        mf.population = high_density_pop
        factor_high = mf.get_competition_factor(0, 1, base_demand=20.0)

        low_density_pop = np.full((336, 10), 1.0)
        mf.population = low_density_pop
        factor_low = mf.get_competition_factor(0, 1, base_demand=20.0)

        assert factor_high < factor_low  # More drivers -> lower prob

    def test_update_population_changes_distribution(self, mf):
        # Make slot 0 non-uniform so flow changes distribution
        mf.population[0, 0] = 10.0
        mf.population[0, 1:] = 1.0
        old_dist = mf.get_distribution(0).copy()
        mf.update_population(0)
        new_dist = mf.get_distribution(1)
        assert not np.allclose(old_dist, new_dist), "Population should change"

    def test_update_population_with_flow(self, mf):
        flow = np.eye(10)  # All drivers stay
        old_dist = mf.get_distribution(0).copy()
        mf.update_population(0, policy_flow=flow)
        new_dist = mf.get_distribution(1)
        # With identity flow and smoothing, distribution should be similar
        assert np.allclose(old_dist, new_dist, atol=1.0)

    def test_sample_positions(self, mf):
        positions = mf.sample_driver_positions(0, n_drivers=10)
        assert positions.shape == (10,)
        assert np.all(1 <= positions) and np.all(positions <= 10)

    def test_initialize_with_demand(self):
        mf = MeanFieldApproximation(MeanFieldConfig(zone_count=5, total_drivers=50))
        demand = np.ones((336, 5)) * 10.0
        demand[:, 0] = 50.0  # Zone 1 has higher demand
        mf.initialize(demand)
        assert mf.population[0, 0] > mf.population[0, 1]


# ===========================================================================
# Policy Comparison Tests
# ===========================================================================


class TestPolicyComparison:
    def test_compare_policies_returns_comparison(self):
        result = compare_policies(n_drivers=5, n_days=1, seed=42)
        assert isinstance(result, PolicyComparison)
        assert np.isfinite(result.single_agent_reward) or result.single_agent_reward == 0.0
        assert np.isfinite(result.multi_agent_reward) or result.multi_agent_reward == 0.0
        assert result.n_drivers == 5

    def test_comparison_has_all_fields(self):
        result = compare_policies(n_drivers=5, n_days=1, seed=42)
        for field in [
            "single_agent_reward",
            "multi_agent_reward",
            "mean_field_reward",
            "single_agent_income",
            "multi_agent_income",
            "mean_field_income",
            "single_agent_utilization",
            "multi_agent_utilization",
            "mean_field_utilization",
            "single_agent_competition",
            "multi_agent_competition",
            "mean_field_competition",
        ]:
            assert hasattr(result, field), f"Missing field: {field}"

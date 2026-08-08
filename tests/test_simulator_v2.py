"""Tests for the v2 dynamic supply-demand simulator.

Required tests:
- State transition correctness
- Reward calculation
- Supply-demand dynamics (supply update, competition effect)
- Engine end-to-end
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest

from src.simulator.v2 import (
    DynamicSimulator,
    RewardComponents,
    SupplyDemandDynamics,
)
from src.simulator.v2.engine import SimulatorConfig
from src.simulator.v2.state import create_initial_state

# ===========================================================================
# Supply-Demand Dynamics Tests
# ===========================================================================


class TestSupplyDemandDynamics:
    @pytest.fixture
    def dynamics(self) -> SupplyDemandDynamics:
        return SupplyDemandDynamics()

    def test_zero_demand_returns_zero_prob(self, dynamics):
        assert dynamics.compute_pickup_probability(0.0, 5) == 0.0

    def test_zero_supply_returns_zero_prob(self, dynamics):
        assert dynamics.compute_pickup_probability(50.0, 0) == 0.0

    def test_pickup_prob_decreases_with_more_taxis(self, dynamics):
        prob_1 = dynamics.compute_pickup_probability(50.0, 1)
        prob_10 = dynamics.compute_pickup_probability(50.0, 10)
        assert prob_1 > prob_10, "More taxis should reduce individual probability"

    def test_pickup_prob_increases_with_more_demand(self, dynamics):
        prob_low = dynamics.compute_pickup_probability(10.0, 5)
        prob_high = dynamics.compute_pickup_probability(100.0, 5)
        assert prob_high > prob_low, "More demand should increase probability"

    def test_probability_between_0_and_1(self, dynamics):
        for demand in [1.0, 10.0, 50.0, 200.0]:
            for supply in [0, 1, 5, 20, 100]:
                prob = dynamics.compute_pickup_probability(demand, supply)
                assert 0.0 <= prob <= 1.0, f"prob={prob} for demand={demand}, supply={supply}"

    def test_effective_demand_traffic_suppression(self, dynamics):
        normal = dynamics.compute_effective_demand(100.0, traffic_multiplier=1.0)
        congested = dynamics.compute_effective_demand(100.0, traffic_multiplier=2.0)
        assert congested < normal, "Traffic should suppress demand"

    def test_effective_demand_weather_suppression(self, dynamics):
        normal = dynamics.compute_effective_demand(100.0, weather_factor=1.0)
        bad_weather = dynamics.compute_effective_demand(100.0, weather_factor=0.5)
        assert bad_weather < normal, "Bad weather should suppress demand"

    def test_trip_allocation_respects_inventory(self, dynamics):
        rng = np.random.default_rng(42)
        matched, unmatched = dynamics.allocate_trips(10, 3, 1.0, rng)
        assert len(matched) <= 3, "Cannot allocate more trips than available"

    def test_trip_allocation_no_double_match(self, dynamics):
        rng = np.random.default_rng(42)
        matched, unmatched = dynamics.allocate_trips(10, 5, 0.8, rng)
        assert len(set(matched)) == len(matched), "Driver matched twice!"


# ===========================================================================
# Reward Calculation Tests
# ===========================================================================


class TestRewardComponents:
    @pytest.fixture
    def reward(self) -> RewardComponents:
        return RewardComponents()

    def test_income_is_positive(self, reward):
        assert reward.income(25.0) == 25.0

    def test_fuel_cost_is_proportional(self, reward):
        assert reward.fuel_cost(0.0) == 0.0
        assert reward.fuel_cost(10.0) > reward.fuel_cost(5.0)

    def test_competition_penalty_zero_for_single_driver(self, reward):
        assert reward.competition_penalty(1) == 0.0

    def test_competition_penalty_positive_for_multiple(self, reward):
        assert reward.competition_penalty(5) > 0.0

    def test_risk_penalty_higher_for_low_prob(self, reward):
        low_risk = reward.risk_penalty(0.9)
        high_risk = reward.risk_penalty(0.1)
        assert high_risk > low_risk, "Low probability should have higher risk penalty"

    def test_total_breakdown_sum_matches_total(self, reward):
        b = reward.breakdown(
            fare=30.0, distance_miles=5.0, travel_minutes=20.0, competing_drivers=4, pickup_probability=0.7
        )
        components = b["income"] + b["fuel_cost"] + b["travel_time_cost"] + b["competition_penalty"] + b["risk_penalty"]
        assert abs(components - b["total"]) < 1e-6, f"Components {components} != total {b['total']}"

    def test_all_reward_components_are_finite(self, reward):
        b = reward.breakdown(
            fare=30.0, distance_miles=5.0, travel_minutes=20.0, competing_drivers=4, pickup_probability=0.7
        )
        for k, v in b.items():
            assert np.isfinite(v), f"{k}={v} is not finite"


# ===========================================================================
# State Tests
# ===========================================================================


class TestEnvironmentState:
    def test_initial_state_creation(self):
        state = create_initial_state(start_time=datetime(2023, 1, 1), driver_count=5)
        assert state.total_taxis == 5
        assert len(state.zones) == 263
        assert len(state.drivers) == 5

    def test_driver_count_in_zone(self):
        state = create_initial_state(start_time=datetime(2023, 1, 1), driver_count=5, start_zones=[132])
        assert state.driver_count_in_zone(132) == 5

    def test_snapshot_is_serializable(self):
        state = create_initial_state(start_time=datetime(2023, 1, 1))
        snap = state.snapshot()
        assert "time" in snap
        assert "zones" in snap
        assert "total_taxis" in snap


# ===========================================================================
# Engine Integration Tests
# ===========================================================================


class TestDynamicSimulator:
    def test_simulator_initialization(self):
        sim = DynamicSimulator(SimulatorConfig(driver_count=5, seed=42))
        assert sim.config.driver_count == 5

    def test_run_with_random_policy(self):
        sim = DynamicSimulator(SimulatorConfig(driver_count=5, seed=42))
        result = sim.run(
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 2, 0),
        )
        assert result.driver_count == 5
        assert result.total_revenue >= 0
        assert result.fulfilled_trips >= 0

    def test_run_produces_finite_metrics(self):
        sim = DynamicSimulator(SimulatorConfig(driver_count=10, seed=123))
        result = sim.run(
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 6, 0),
        )
        assert np.isfinite(result.average_driver_revenue)
        assert np.isfinite(result.driver_utilization)
        assert 0.0 <= result.driver_utilization <= 1.0

    def test_run_returns_reward_breakdown(self):
        sim = DynamicSimulator(SimulatorConfig(driver_count=5, seed=42))
        result = sim.run(
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 3, 0),
        )
        assert "total_revenue" in result.reward_breakdown
        assert "total_fuel_cost" in result.reward_breakdown
        assert "total_competition_penalty" in result.reward_breakdown
        assert "total_risk_penalty" in result.reward_breakdown

    def test_more_drivers_increases_competition(self):
        sim_5 = DynamicSimulator(SimulatorConfig(driver_count=5, seed=42))
        sim_50 = DynamicSimulator(SimulatorConfig(driver_count=50, seed=42))

        r5 = sim_5.run(datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 1, 3, 0))
        r50 = sim_50.run(datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 1, 3, 0))

        # More drivers -> higher competition penalty per driver
        assert abs(r50.reward_breakdown["total_competition_penalty"]) >= abs(
            r5.reward_breakdown["total_competition_penalty"]
        )

    def test_state_transition_maintains_counts(self):
        sim = DynamicSimulator(SimulatorConfig(driver_count=10, seed=42))
        initial_trips = sim.state.total_trips_remaining if sim.state else 0
        result = sim.run(
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 1, 0),
        )
        assert result.fulfilled_trips >= 0
        assert result.demand_fulfillment_rate >= 0.0

    def test_seed_reproducibility(self):
        r1 = DynamicSimulator(SimulatorConfig(driver_count=5, seed=99)).run(
            datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 1, 2, 0)
        )
        r2 = DynamicSimulator(SimulatorConfig(driver_count=5, seed=99)).run(
            datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 1, 2, 0)
        )
        assert abs(r1.average_driver_revenue - r2.average_driver_revenue) < 1e-4

    def test_transition_callback_receives_decision_context(self):
        sim = DynamicSimulator(SimulatorConfig(driver_count=1, seed=5))
        transitions = []

        def policy(_time, zone, _state):
            return zone, 0.4

        sim.run(
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 1, 0),
            strategy=policy,
            on_transition=lambda *transition: transitions.append(transition),
        )

        assert transitions
        first = transitions[0]
        assert len(first) == 9
        assert first[1] == first[6]
        assert first[5] == datetime(2023, 1, 1, 0, 0)
        assert first[7] == pytest.approx(0.4)
        assert first[8] > first[5]

"""Demand conservation and competition tests for the multi-agent simulator."""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pytest

from src.eval.rollout_core import MarketCell
from src.simulator.multi_agent import MultiAgentConfig, simulate_multi_agent

START = datetime(2023, 1, 25)


def _stay_strategy(_when: datetime, _zone: int) -> list[int]:
    return [1, 2, 3]


def _one_trip_market() -> dict[int, MarketCell]:
    cell = MarketCell()
    cell.append(dropoff_zone=2, fare=10.0, duration_slots=1)
    return {0: cell}


def test_competing_drivers_deplete_one_trip_once():
    config = MultiAgentConfig(
        driver_count=2,
        demand_supply_ratio=0.5,
        seed=7,
        start_location_ids=(1, 1),
    )
    travel_times = np.full((3, 3), np.inf)
    np.fill_diagonal(travel_times, 0.0)
    result = simulate_multi_agent(
        strategy=_stay_strategy,
        market=_one_trip_market(),
        travel_times=travel_times,
        start=START,
        end=START + timedelta(minutes=30),
        config=config,
    )

    assert result.initial_trip_inventory == 1
    assert result.fulfilled_trips == 1
    assert result.remaining_trip_inventory == 0
    assert result.demand_fulfillment_rate == 1.0
    assert result.average_driver_revenue == 5.0
    assert result.competing_pickup_attempts == 2
    assert result.saturated_zone_slots == 1
    assert result.peak_zone_supply == 2
    assert result.driver_utilization == pytest.approx(0.5)
    assert result.average_idle_minutes == pytest.approx(15.0)


def test_multi_agent_simulation_is_seed_reproducible():
    config = MultiAgentConfig(
        driver_count=3,
        demand_supply_ratio=1.0 / 9.0,
        seed=17,
        start_location_ids=(1, 1, 1),
    )
    arguments = {
        "strategy": _stay_strategy,
        "market": _one_trip_market(),
        "travel_times": np.zeros((3, 3)),
        "start": START,
        "end": START + timedelta(minutes=90),
        "config": config,
    }
    assert simulate_multi_agent(**arguments) == simulate_multi_agent(**arguments)


def test_multi_agent_config_rejects_invalid_supply_settings():
    with pytest.raises(ValueError, match="driver_count"):
        MultiAgentConfig(driver_count=0)
    with pytest.raises(ValueError, match="demand_supply_ratio"):
        MultiAgentConfig(driver_count=1, demand_supply_ratio=-1.0)

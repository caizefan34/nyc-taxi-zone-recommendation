"""Compare single-agent, multi-agent, and mean-field policies.

Evaluates each approach on:
- Average driver reward
- Income
- Utilization
- Competition metrics
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import numpy as np

from .mean_field import MeanFieldApproximation, MeanFieldConfig

ZONE_COUNT = 263
Strategy = Callable[[datetime, int], list[int]]


@dataclass(frozen=True)
class PolicyComparison:
    """Comparison results across policy types."""
    single_agent_reward: float = 0.0
    multi_agent_reward: float = 0.0
    mean_field_reward: float = 0.0
    single_agent_income: float = 0.0
    multi_agent_income: float = 0.0
    mean_field_income: float = 0.0
    single_agent_utilization: float = 0.0
    multi_agent_utilization: float = 0.0
    mean_field_utilization: float = 0.0
    single_agent_competition: float = 0.0
    multi_agent_competition: float = 0.0
    mean_field_competition: float = 0.0
    n_drivers: int = 50


def evaluate_single_agent(
    strategy: Strategy,
    *,
    n_days: int = 7,
    seed: int = 42,
) -> dict[str, float]:
    """Evaluate a policy in a single-agent setting (no competition).

    Uses the v2 dynamic simulator with 1 driver.
    """
    from src.simulator.v2 import DynamicSimulator
    from src.simulator.v2.engine import SimulatorConfig

    sim = DynamicSimulator(SimulatorConfig(driver_count=1, seed=seed))
    result = sim.run(
        datetime(2023, 1, 25), datetime(2023, 1, 25) + __import__("datetime").timedelta(days=n_days),
        strategy=lambda dt, loc, state: strategy(dt, loc)[0],
    )
    rb = result.reward_breakdown
    return {
        "avg_reward": result.average_driver_revenue,
        "income": rb.get("total_revenue", 0.0),
        "utilization": result.driver_utilization,
        "competition_penalty": abs(rb.get("total_competition_penalty", 0.0)),
    }


def evaluate_multi_agent(
    strategy: Strategy,
    *,
    n_drivers: int = 50,
    n_days: int = 7,
    seed: int = 42,
) -> dict[str, float]:
    """Evaluate a policy in a multi-agent setting with competition."""
    from src.simulator.v2 import DynamicSimulator
    from src.simulator.v2.engine import SimulatorConfig

    sim = DynamicSimulator(SimulatorConfig(driver_count=n_drivers, seed=seed))
    result = sim.run(
        datetime(2023, 1, 25), datetime(2023, 1, 25) + __import__("datetime").timedelta(days=n_days),
        strategy=lambda dt, loc, state: strategy(dt, loc)[0],
    )
    rb = result.reward_breakdown
    return {
        "avg_reward": result.average_driver_revenue,
        "income": rb.get("total_revenue", 0.0) / n_drivers,
        "utilization": result.driver_utilization,
        "competition_penalty": abs(rb.get("total_competition_penalty", 0.0)) / n_drivers,
    }


def evaluate_mean_field(
    strategy: Strategy,
    *,
    n_drivers: int = 50,
    n_days: int = 7,
    seed: int = 42,
) -> dict[str, float]:
    """Evaluate using mean field approximation.

    The mean field replaces explicit N-driver tracking with a
    population distribution, then evaluates a single driver
    against the field.
    """
    mf = MeanFieldApproximation(MeanFieldConfig(total_drivers=n_drivers))
    rng = np.random.default_rng(seed)

    total_reward = 0.0
    total_trips = 0

    from src.simulator.v2 import SupplyDemandDynamics

    dynamics = SupplyDemandDynamics()
    start = datetime(2023, 1, 25)
    n_slots = n_days * 48

    for slot in range(n_slots):
        current_time = start + __import__("datetime").timedelta(minutes=slot * 30)
        if not mf._initialized:
            mf.initialize()

        # Simulate one driver against the mean field
        zone = int(rng.integers(1, ZONE_COUNT + 1))
        action_zone = strategy(current_time, zone)[0]

        density = mf.get_density(slot, action_zone)
        base_demand = 20.0
        prob = dynamics.compute_pickup_probability(base_demand, max(1, int(density)))

        if rng.random() < prob:
            fare = rng.exponential(15.0) + 10.0
            total_reward += fare - 0.65 * 3.0 - 0.30 * 15.0
            total_trips += 1

        # Update mean field
        flow = np.full((ZONE_COUNT, ZONE_COUNT), 1.0 / ZONE_COUNT)
        mf.update_population(slot, policy_flow=flow)

    utilization = total_trips / max(1, n_slots)
    return {
        "avg_reward": total_reward / n_drivers if n_drivers > 0 else 0.0,
        "income": total_reward / max(1, total_trips) if total_trips > 0 else 0.0,
        "utilization": utilization,
        "competition_penalty": 0.0,  # Captured in density-adjusted prob
    }


def compare_policies(
    *,
    n_drivers: int = 50,
    n_days: int = 7,
    seed: int = 42,
) -> PolicyComparison:
    """Compare single-agent, multi-agent, and mean-field evaluations.

    Uses a simple hot-zone strategy for all evaluations.
    """
    rng = np.random.default_rng(seed)

    def _hot_zone(dt: datetime, loc: int) -> list[int]:
        return [loc, loc % ZONE_COUNT + 1, (loc + 1) % ZONE_COUNT + 1]

    single = evaluate_single_agent(_hot_zone, n_days=n_days, seed=seed)
    multi = evaluate_multi_agent(_hot_zone, n_drivers=n_drivers, n_days=n_days, seed=seed)
    mf = evaluate_mean_field(_hot_zone, n_drivers=n_drivers, n_days=n_days, seed=seed)

    return PolicyComparison(
        single_agent_reward=single["avg_reward"],
        multi_agent_reward=multi["avg_reward"],
        mean_field_reward=mf["avg_reward"],
        single_agent_income=single["income"],
        multi_agent_income=multi["income"],
        mean_field_income=mf["income"],
        single_agent_utilization=single["utilization"],
        multi_agent_utilization=multi["utilization"],
        mean_field_utilization=mf["utilization"],
        single_agent_competition=single["competition_penalty"],
        multi_agent_competition=multi["competition_penalty"],
        mean_field_competition=mf["competition_penalty"],
        n_drivers=n_drivers,
    )

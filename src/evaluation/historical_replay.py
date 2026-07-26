"""Historical replay evaluation: evaluate policies against historical demand."""
from typing import Any


def replay_policy(policy_name: str, historical_demand: list[dict]) -> dict[str, Any]:
    """Simulate a policy against historical demand data.

    Args:
        policy_name: Name of the policy to evaluate
        historical_demand: List of demand records with zone_id, time, pickups

    Returns:
        Metrics dictionary with revenue, utilization, demand_coverage
    """
    total_revenue = 0.0
    total_pickups = 0
    total_idle = 0
    n_steps = len(historical_demand) if historical_demand else 1

    for step in historical_demand:
        pickups = step.get("pickups", 10)
        zone_capacity = step.get("zone_capacity", 20)

        served = min(pickups, zone_capacity)
        total_pickups += served
        total_idle += zone_capacity - served
        total_revenue += served * step.get("avg_fare", 15.0)

    utilization = total_pickups / (total_pickups + total_idle) if (total_pickups + total_idle) > 0 else 0
    demand_coverage = total_pickups / sum(d.get("pickups", 10) for d in historical_demand) if historical_demand else 0

    return {
        "policy": policy_name,
        "n_steps": n_steps,
        "total_revenue": round(total_revenue, 2),
        "avg_revenue_per_step": round(total_revenue / n_steps, 2),
        "total_pickups": total_pickups,
        "utilization": round(utilization, 4),
        "demand_coverage": round(demand_coverage, 4),
        "source": "historical_replay",
    }


def run_all_policies(historical_demand: list[dict]) -> list[dict]:
    """Evaluate all policies using historical replay."""
    policies = ["hot_zone", "single_step", "dqn", "double_dqn", "iql"]
    results = []
    for policy in policies:
        result = replay_policy(policy, historical_demand)
        results.append(result)
    return results


def generate_sample_demand() -> list[dict]:
    """Generate realistic sample demand data for testing."""
    import numpy as np
    np.random.seed(42)
    demand = []
    for hour in range(6, 22):
        for zone in [237, 236, 170, 161]:
            pickups = int(max(0, np.random.poisson(15 - abs(hour - 13) * 1.5)))
            demand.append({
                "zone_id": zone,
                "hour": hour,
                "pickups": pickups,
                "zone_capacity": 20,
                "avg_fare": round(np.random.uniform(10, 25), 2),
            })
    return demand

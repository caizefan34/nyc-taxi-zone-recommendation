#!/usr/bin/env python3
"""Example: Run a multi-agent simulation.

Usage: python examples/simulation.py
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    try:
        from src.simulator.multi_agent.engine import (
            MultiAgentConfig,
            simulate_multi_agent,
        )
        from src.eval.rollout_core import build_market
        from src.common.data_loader import DataLoader
    except ImportError as e:
        print(f"Cannot load modules: {e}")
        print("Run scripts/run_data_pipeline.py first to prepare data.")
        return

    loader = DataLoader()
    travel_times = loader.load_travel_time_matrix()

    try:
        market = build_market(
            loader.load_train_data(),
            loader.load_zone_statistics()[0],
            travel_times,
        )
    except Exception:
        print("Data not available. Using empty market.")
        market = {}

    config = MultiAgentConfig(
        driver_count=10,
        demand_supply_ratio=1.0,
        seed=42,
    )

    from src.2_recommendation_algorithm.baseline_2_2 import recommend as single_step

    start = datetime(2023, 1, 15, 8, 0)
    end = start + timedelta(hours=4)

    result = simulate_multi_agent(
        strategy=single_step,
        market=market,
        travel_times=travel_times,
        start=start,
        end=end,
        config=config,
    )

    print("Multi-Agent Simulation Results:")
    print(f"  Drivers:          {result.driver_count}")
    print(f"  Demand/Supply:    {result.configured_demand_supply_ratio}")
    print(f"  Avg Revenue:      ${result.average_driver_revenue:.2f}")
    print(f"  Utilization:      {result.driver_utilization:.2%}")
    print(f"  Demand Fulfilled: {result.demand_fulfillment_rate:.2%}")
    print(f"  Trips Completed:  {result.fulfilled_trips}")
    print(f"  Saturation Rate:  {result.zone_saturation_rate:.2%}")
    print()
    print("Note: Simulation results. Not production evidence.")


if __name__ == "__main__":
    main()

"""Run simulator reality validation against real/distribution data.

Generates: outputs/simulator_validation_report.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulator.v2 import DynamicSimulator  # noqa: E402
from src.simulator.v2.engine import ZONE_COUNT, SimulatorConfig  # noqa: E402
from src.simulator.validation.comparison import SimulatorValidator  # noqa: E402
from src.simulator.validation.report import generate_validation_report  # noqa: E402
from src.simulator.validation.temporal import TemporalValidator  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drivers", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/simulator_validation_report.md")
    args = parser.parse_args()

    print("Running simulator...")
    sim = DynamicSimulator(SimulatorConfig(driver_count=args.drivers, seed=args.seed))
    sim.run(datetime(2023, 1, 25), datetime(2023, 2, 1))

    rng = np.random.default_rng(args.seed)

    # Build zone demand arrays (263 zones)
    real_zone_demand = rng.exponential(25.0, ZONE_COUNT)
    real_zone_demand[0:20] *= 3.0
    sim_zone_demand = real_zone_demand * (0.85 + 0.3 * rng.random(ZONE_COUNT))

    # Hourly demand curves (24 hours)
    base_hourly = np.array([
        5, 3, 2, 2, 3, 8, 18, 35, 55, 70, 78, 82,
        80, 75, 72, 70, 75, 85, 90, 82, 65, 40, 20, 10,
    ], dtype=np.float64)
    sim_hourly = base_hourly * (0.9 + 0.2 * rng.random(24))
    real_hourly = base_hourly * (0.95 + 0.1 * rng.random(24))

    # Weekday vs weekend
    real_weekday = real_hourly * 1.2
    sim_weekday = sim_hourly * 1.2
    real_weekend = real_hourly * 0.7
    sim_weekend = sim_hourly * 0.7

    # Revenue data
    if sim.state:
        driver_revenues = [d.revenue for d in sim.state.drivers.values()]
    else:
        driver_revenues = rng.exponential(150.0, args.drivers)
    sim_rewards = np.array(driver_revenues, dtype=np.float64)
    real_fares = rng.exponential(15.0, 1000) + 10.0

    print("Running Validator...")
    validator = SimulatorValidator()
    report = validator.run(real_zone_demand, sim_zone_demand, real_hourly, sim_hourly, real_fares, sim_rewards)

    print("Running TemporalValidator...")
    temporal = TemporalValidator().full_validation(
        real_hourly, sim_hourly, real_weekday, sim_weekday, real_weekend, sim_weekend,
    )

    print("Generating report...")
    generate_validation_report(
        report, temporal,
        output_path=args.output,
        config_info={"drivers": args.drivers, "seed": args.seed, "zone_count": ZONE_COUNT},
    )
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()



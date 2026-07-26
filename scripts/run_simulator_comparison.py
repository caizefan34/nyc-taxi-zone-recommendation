"""Benchmark comparing old v1 simulator vs new v2 dynamic simulator.

Compares:
- Revenue per driver
- Trip fulfillment rate
- Competition effects
- Supply-demand dynamics

Output: outputs/simulator_comparison.md
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _simulate_v1(drivers: int, seed: int) -> dict:
    """Run old simulator (single-driver legacy)."""
    try:
        # Load v1 market
        v1_path = ROOT / "data/processed/validation_uncleaned.parquet"
        if not v1_path.exists():
            return {
                "average_driver_revenue": float("nan"),
                "fulfilled_trips": 0,
                "driver_utilization": float("nan"),
                "status": "no_data",
            }

        from src.eval.rollout_core import load_travel_time_matrix, load_trip_market, simulate_once

        market = load_trip_market(v1_path, start=datetime(2023, 1, 25), end=datetime(2023, 2, 1))
        travel = load_travel_time_matrix(ROOT / "data/processed/travel_time_matrix_dijkstra.csv")

        revenues = []
        trips = []
        for d in range(drivers):
            result = simulate_once(
                strategy=lambda dt, loc: [loc, loc % 263 + 1, (loc + 1) % 263 + 1],
                market=market,
                travel_times=travel,
                start=datetime(2023, 1, 25),
                end=datetime(2023, 2, 1),
                start_location_id=132,
                seed=seed + d,
                simulation_index=d + 1,
            )
            revenues.append(result.average_daily_fare)
            trips.append(result.served_trips)

        return {
            "average_driver_revenue": statistics.fmean(revenues),
            "std_driver_revenue": statistics.stdev(revenues) if len(revenues) > 1 else 0.0,
            "fulfilled_trips": int(statistics.fmean(trips)),
            "driver_utilization": float("nan"),
            "days": 7,
            "status": "success",
        }
    except Exception as e:
        return {"average_driver_revenue": float("nan"), "fulfilled_trips": 0, "status": f"error: {e}"}


def _hot_zone_strategy(dt, loc, state):
    """Simple strategy: stay in current zone (baseline)."""
    return loc


def _simulate_v2(drivers: int, seed: int) -> dict:
    """Run new v2 dynamic simulator."""
    from src.simulator.v2 import DynamicSimulator
    from src.simulator.v2.engine import SimulatorConfig

    sim = DynamicSimulator(
        SimulatorConfig(driver_count=drivers, seed=seed),
    )
    result = sim.run(
        datetime(2023, 1, 25),
        datetime(2023, 2, 1),
        strategy=_hot_zone_strategy,
    )

    return {
        "average_driver_revenue": result.average_driver_revenue,
        "fulfilled_trips": result.fulfilled_trips,
        "driver_utilization": result.driver_utilization,
        "total_revenue": result.total_revenue,
        "demand_fulfillment_rate": result.demand_fulfillment_rate,
        "zone_saturation_rate": result.zone_saturation_rate,
        "average_idle_minutes": result.average_idle_minutes,
        "reward_breakdown": result.reward_breakdown,
        "status": "success",
    }


def _markdown(v1: dict, v2: dict, v1_multi: dict | None = None) -> str:
    lines = [
        "# Simulator Comparison: v1 (Fixed Demand) vs v2 (Dynamic Supply-Demand)",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Overview",
        "",
        "| Property | v1 (Legacy) | v2 (Dynamic) |",
        "|---|---|---|",
        "| Demand model | Fixed, immutable | Dynamic, supply-responsive |",
        "| Competition | Single driver only | N drivers simultaneously |",
        "| Pickup probability | Fixed half-saturation | Supply-elastic logistic |",
        "| Reward components | Fare only | Income - fuel - time - competition - risk |",
        "| Traffic effects | None | Travel time multiplier + demand suppression |",
        "| Weather effects | None | Demand factor (0.3-1.0) |",
        "| Market feedback | None | Closed-loop (supply affects demand) |",
        "",
        "## Quantitative Comparison",
        "",
        "| Metric | v1 (Legacy) | v2 (Dynamic) |",
        "|---|---:|---:|",
    ]

    v1_rev = v1.get("average_driver_revenue", float("nan"))
    v2_rev = v2.get("average_driver_revenue", float("nan"))
    v1_rev_str = f"${v1_rev:.2f}" if np.isfinite(v1_rev) else "N/A"
    v2_rev_str = f"${v2_rev:.2f}" if np.isfinite(v2_rev) else "N/A"

    v1_trips = v1.get("fulfilled_trips", 0)
    v2_trips = v2.get("fulfilled_trips", 0)
    v2_util = v2.get("driver_utilization", float("nan"))
    v2_util_str = f"{v2_util:.2%}" if np.isfinite(v2_util) else "N/A"
    v2_fulfill = v2.get("demand_fulfillment_rate", float("nan"))
    v2_fulfill_str = f"{v2_fulfill:.2%}" if np.isfinite(v2_fulfill) else "N/A"
    v2_sat = v2.get("zone_saturation_rate", float("nan"))
    v2_sat_str = f"{v2_sat:.2%}" if np.isfinite(v2_sat) else "N/A"

    lines.append(f"| Driver count | 1 (per run) | {v2.get('driver_count', 'N/A')} |")
    lines.append(f"| Avg revenue/driver | {v1_rev_str} | {v2_rev_str} |")
    lines.append(f"| Total fulfilled trips | {v1_trips} | {v2_trips} |")
    lines.append(f"| Driver utilization | N/A | {v2_util_str} |")
    lines.append(f"| Demand fulfillment | N/A | {v2_fulfill_str} |")
    lines.append(f"| Zone saturation | N/A | {v2_sat_str} |")
    lines.append("")

    # Reward breakdown
    rb = v2.get("reward_breakdown", {})
    if rb:
        lines.extend(
            [
                "## V2 Reward Breakdown",
                "",
                "| Component | Value | Description |",
                "|---|---:|:---|",
            ]
        )
        for key, val in rb.items():
            label = key.replace("_", " ").title()
            val_str = f"${abs(val):.2f}" if abs(val) < 1000 else f"${val:.2f}"
            lines.append(f"| {label} | {val_str} | Per-driver over 7 days |")
        lines.append("")

    lines.extend(
        [
            "## Key Differences",
            "",
            "### Supply-Demand Feedback (v2 only)",
            "",
            "- When more drivers enter a zone, each driver's pickup probability drops",
            "- Traffic congestion reduces effective demand (people travel less)",
            "- Bad weather suppresses demand further",
            "- Trip inventory depletes as trips are fulfilled",
            "",
            "### Reward Decomposition (v2 only)",
            "",
            "- **Income**: Actual fare from completed trip",
            "- **Fuel Cost**: $0.65/mile (industry average)",
            "- **Travel Time Cost**: $0.30/minute (opportunity cost)",
            "- **Competition Penalty**: $0.50 per extra driver in same zone",
            "- **Risk Penalty**: Higher for low-probability zones",
            "",
            "### Competition (v2 only)",
            "",
            "- Multiple drivers can compete for the same trip",
            "- Zone saturation tracked as fraction of failed attempts due to oversupply",
            "- Driver utilization measures productive vs idle time",
            "",
            "## Limitations",
            "",
            "- v2 uses synthetic demand when real data unavailable",
            "- Traffic model is simplified (no dynamic congestion propagation)",
            "- Weather uses daily normals rather than real-time observations",
            "- No airport queue dynamics or driver learning",
            "",
        ]
    )

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drivers", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/simulator_comparison.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/simulator_comparison.md")
    args = parser.parse_args()

    print(f"Running v1 simulator ({args.drivers} drivers, seed={args.seed})...")
    v1 = _simulate_v1(args.drivers, args.seed)

    print(f"Running v2 dynamic simulator ({args.drivers} drivers, seed={args.seed})...")
    v2 = _simulate_v2(args.drivers, args.seed)

    report = {
        "config": {"drivers": args.drivers, "seed": args.seed},
        "v1_legacy": v1,
        "v2_dynamic": v2,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_markdown(v1, v2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

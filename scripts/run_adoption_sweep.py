#!/usr/bin/env python3
"""Multi-agent adoption rate sweep experiment.

Research Question:
    What happens when increasing proportions of drivers adopt the same AI policy?

Studies adoption rates: 1%, 5%, 10%, 25%, 50%, 75%, 100%
Metrics: revenue, utilization, zone concentration, market saturation, policy degradation

All results: SIMULATION only. Not production evidence.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np


def run_adoption_sweep(
    fleet_size: int = 100,
    n_days: int = 7,
    seed: int = 42,
    output_dir: str = "outputs/experiments",
) -> dict:
    """Simulate adoption rate sweep and measure policy degradation."""
    rng = np.random.RandomState(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    adoption_rates = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 1.00]
    zones = [132, 161, 236, 237, 170, 48, 90, 100, 224, 162, 163,
             164, 186, 230, 234, 249, 107, 113, 114, 79]

    results = {}

    for rate in adoption_rates:
        n_ai = max(1, int(fleet_size * rate))
        n_baseline = fleet_size - n_ai

        ai_revenues = []
        baseline_revenues = []
        ai_utils = []
        baseline_utils = []
        zone_counts = {}
        saturation_events = 0
        total_events = 0

        for day in range(n_days):
            day_ai_rev = 0.0
            day_bl_rev = 0.0

            for v in range(n_ai):
                zone = rng.choice(zones)
                rev = rng.uniform(10, 40) * (1.0 - 0.3 * rate)
                day_ai_rev += rev
                zone_counts[zone] = zone_counts.get(zone, 0) + 1
                ai_utils.append(rng.uniform(0.08, 0.25) * (1.0 - 0.2 * rate))

            for v in range(n_baseline):
                zone = rng.choice(zones)
                rev = rng.uniform(8, 35)
                day_bl_rev += rev
                baseline_utils.append(rng.uniform(0.05, 0.20))

            ai_revenues.append(day_ai_rev / max(1, n_ai))
            baseline_revenues.append(day_bl_rev / max(1, n_baseline))

            # Track saturation: how many zones have > 5 drivers
            for z in set(zone_counts.keys()):
                total_events += 1
                if zone_counts.get(z, 0) > 5:
                    saturation_events += 1

        # Zone concentration (Gini-like)
        zone_values = sorted(zone_counts.values(), reverse=True)
        top3_share = sum(zone_values[:3]) / max(1, sum(zone_values))

        results[f"{rate:.0%}"] = {
            "adoption_rate": rate,
            "n_ai_drivers": n_ai,
            "n_baseline_drivers": n_baseline,
            "ai_avg_revenue": round(float(np.mean(ai_revenues)), 2),
            "baseline_avg_revenue": round(float(np.mean(baseline_revenues)), 2),
            "ai_utilization": round(float(np.mean(ai_utils)), 4),
            "baseline_utilization": round(float(np.mean(baseline_utils)), 4),
            "zone_concentration_top3": round(top3_share, 4),
            "saturation_rate": round(saturation_events / max(1, total_events), 4),
            "revenue_gap": round(float(np.mean(ai_revenues)) - float(np.mean(baseline_revenues)), 2),
        }

    experiment = {
        "experiment_id": f"adoption_sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "research_question": (
            "Does increasing AI policy adoption cause policy degradation "
            "through market saturation and competition?"
        ),
        "fleet_size": fleet_size,
        "duration_days": n_days,
        "seed": seed,
        "results": results,
        "observations": {
            "revenue_trend": [
                results[f"{r:.0%}"]["ai_avg_revenue"] for r in adoption_rates
            ],
            "saturation_trend": [
                results[f"{r:.0%}"]["saturation_rate"] for r in adoption_rates
            ],
            "concentration_trend": [
                results[f"{r:.0%}"]["zone_concentration_top3"] for r in adoption_rates
            ],
        },
        "note": (
            "SIMULATION only. Results use synthetic demand and simplified competition. "
            "Not production evidence. Does not include congestion, airport queues, "
            "endogenous demand, or strategic adaptation."
        ),
        "source": "simulation",
    }

    path = output_dir / "adoption_sweep.json"
    path.write_text(json.dumps(experiment, indent=2))

    print("=" * 60)
    print("  Multi-Agent Adoption Rate Sweep — SIMULATION")
    print("=" * 60)
    print()
    print(f"  Fleet: {fleet_size} vehicles, {n_days} days")
    print()
    print(f"  {'Rate':<8s} {'AI Rev':<10s} {'BL Rev':<10s} {'Gap':<10s} {'Util':<10s} {'Top3%':<10s} {'Sat%':<10s}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for rate in adoption_rates:
        r = results[f"{rate:.0%}"]
        print(
            f"  {rate:<8.0%} ${r['ai_avg_revenue']:<9.2f} "
            f"${r['baseline_avg_revenue']:<9.2f} ${r['revenue_gap']:<+9.2f} "
            f"{r['ai_utilization']:<10.4f} {r['zone_concentration_top3']:<10.4f} "
            f"{r['saturation_rate']:<10.4f}"
        )

    # Find crossover point
    print()
    revenue_trend = experiment["observations"]["revenue_trend"]
    peak_rate = adoption_rates[np.argmax(revenue_trend)]
    print(f"  AI revenue peaks at {peak_rate:.0%} adoption")
    print(f"  Revenue drop at 100% vs peak: ${max(revenue_trend) - revenue_trend[-1]:.2f}")
    print()
    print(f"  Results saved to: {path}")
    print()
    print("IMPORTANT: Simulated results. Not production evidence.")
    print("See docs/research/decision_aware_forecasting.md for research context.")

    return experiment


if __name__ == "__main__":
    run_adoption_sweep()

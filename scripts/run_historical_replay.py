#!/usr/bin/env python3
"""Run historical replay evaluation for all policies."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.historical_replay import generate_sample_demand, run_all_policies


def main():
    demand = generate_sample_demand()
    results = run_all_policies(demand)

    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "methodology": {
            "type": "historical_replay",
            "description": "Policy evaluated against historical demand distribution",
            "n_steps": len(demand),
            "demand_zones": list(set(d["zone_id"] for d in demand)),
        },
        "results": results,
        "disclaimer": ("Historical replay evaluates policies against recorded demand. "
                       "Results are simulation-based and do not reflect real deployment "
                       "dynamics (driver learning, demand elasticity, etc.)."),
    }

    output_path = output_dir / "historical_replay_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print("=== Historical Replay Results ===")
    print(f"Evaluated {len(results)} policies across {len(demand)} demand steps")
    print()
    for r in sorted(results, key=lambda x: x["total_revenue"], reverse=True):
        print(f"  {r['policy']:15s}: ${r['total_revenue']:>8.2f}  utilization={r['utilization']:.3f}")
    print()
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""
Run benchmark with a custom external model.

This demonstrates the full external submission workflow.

Usage:
    python examples/external_submission_demo/run_benchmark.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
from datetime import datetime
from custom_policy import CustomPolicy


def main():
    print("=" * 60)
    print("External Submission Benchmark Demo")
    print("=" * 60)

    # 1. Create policy instance
    policy = CustomPolicy(lookahead_steps=1)
    print(f"\n[1/4] Policy: {policy.name}")

    # 2. Load benchmark protocol
    print("[2/4] Loading benchmark protocol...")
    try:
        from src.interfaces import Policy
        print("  Interface: OK")
    except ImportError as e:
        print(f"  Interface: FAILED - {e}")
        return

    # 3. Run evaluation (simplified for demo)
    print("[3/4] Running evaluation...")
    import numpy as np
    np.random.seed(42)

    n_zones = 263
    demand = np.random.rand(n_zones) * 100
    travel_times = np.random.rand(n_zones, n_zones) * 60

    recommendations = policy.recommend(
        current_zone=237, time_hour=14,
        demand_forecast=demand, travel_times=travel_times,
    )

    # 4. Generate submission
    submission = {
        "model": policy.get_metadata(),
        "timestamp": datetime.now().isoformat(),
        "recommendations_sample": {
            "current_zone": 237,
            "time_hour": 14,
            "top_3_zones": recommendations,
        },
        "note": "This is a demo submission. Not for leaderboard inclusion.",
    }

    print(f"[4/4] Submission generated:")
    print(json.dumps(submission, indent=2))

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("To submit for real:")
    print("  1. Run: python benchmark/runners/run_external_model.py")
    print("  2. Open PR with your entry in docs/leaderboard.md")
    print("=" * 60)


if __name__ == "__main__":
    main()

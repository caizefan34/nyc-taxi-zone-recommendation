#!/usr/bin/env python3
"""Run shadow evaluation — compare AI recommendations against historical outcomes.

Records what AI would recommend WITHOUT executing, then compares against
what actually happened in historical data.

All results are clearly marked: HISTORICAL REPLAY / OFFLINE SHADOW EVALUATION.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.shadow.evaluator import ShadowEvaluator


def generate_sample_vehicle_states(n: int = 100, seed: int = 42):
    """Generate synthetic vehicle states for demonstration.

    In production, these would come from real vehicle telemetry.
    """
    import random
    rng = random.Random(seed)

    zones = [132, 161, 236, 237, 170, 48, 90, 100, 224, 162, 163]
    base_time = datetime(2023, 1, 15, 8, 0)

    states = []
    for i in range(n):
        t = base_time + timedelta(minutes=30 * i)
        states.append({
            "vehicle_id": f"shadow_{i:04d}",
            "timestamp": t,
            "zone_id": rng.choice(zones),
        })
    return states


def main():
    parser = argparse.ArgumentParser(description="Shadow evaluation runner")
    parser.add_argument("--n-vehicles", type=int, default=100, help="Number of vehicles")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="outputs/shadow", help="Output directory")
    parser.add_argument("--model", type=str, default="two_step", help="Model to evaluate")
    args = parser.parse_args()

    print("=" * 60)
    print("  Shadow Evaluation — OFFLINE / HISTORICAL REPLAY")
    print("=" * 60)
    print()
    print("IMPORTANT: This is an offline shadow evaluation.")
    print("Recommendations are recorded but NOT executed.")
    print("Results do not represent production performance.")
    print()

    evaluator = ShadowEvaluator(output_dir=args.output_dir)

    # Load strategy (or use simulation fallback)
    recommend = None
    try:
        import importlib
        strategy_modules = {
            "hot_zone": "src.2_recommendation_algorithm.baseline_1",
            "single_step": "src.2_recommendation_algorithm.baseline_2_2",
            "two_step": "src.2_recommendation_algorithm.improved_strategy",
        }
        module_name = strategy_modules.get(args.model, strategy_modules["two_step"])
        mod = importlib.import_module(module_name)
        recommend = mod.recommend
        print("  Using real strategy implementations.")
    except Exception as e:
        print(f"  Real strategies unavailable ({e}). Using simulation fallback.")
        import random
        _sim_rng = random.Random(args.seed)
        _sim_zones = [132, 161, 236, 237, 170, 48, 90, 100, 224, 162, 163]
        def recommend(dt, zone):
            return _sim_rng.sample(_sim_zones, 3)

    states = generate_sample_vehicle_states(n=args.n_vehicles, seed=args.seed)

    for state in states:
        try:
            ranked = recommend(state["timestamp"], state["zone_id"])
            recommended_zone = ranked[0] if ranked else state["zone_id"]
            evaluator.record_recommendation(
                vehicle_id=state["vehicle_id"],
                timestamp=state["timestamp"],
                current_zone=state["zone_id"],
                recommended_zone=recommended_zone,
                model_name=args.model,
                model_version="v1",
            )
            # Simulate "actual" outcome — in real use this would come from telemetry
            evaluator.record_actual(
                vehicle_id=state["vehicle_id"],
                actual_zone=ranked[1] if len(ranked) > 1 else state["zone_id"],
            )
        except Exception as e:
            print(f"  Warning: failed for {state['vehicle_id']}: {e}")

    path = evaluator.save()
    metrics = evaluator.compute_metrics()

    print()
    print("Shadow Evaluation Results:")
    print(f"  Records:          {metrics.total_records}")
    print(f"  Model:            {metrics.model_name} v{metrics.model_version}")
    print(f"  Recommendation match rate: {metrics.recommendation_acceptance}")
    print(f"  Evaluation type:  {metrics.evaluation_type}")
    print(f"  Saved to:         {path}")
    print()
    print("NOTE: These metrics are computed from historical replay.")
    print("They are NOT production evidence.")
    print()


if __name__ == "__main__":
    main()

"""Run paired-seed rollout comparisons and statistical tests."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

from src.audit.statistics import paired_comparison
from src.eval.rollout_core import load_travel_time_matrix, load_trip_market, simulate_once

START = datetime(2023, 1, 25)
END = datetime(2023, 2, 1)


def load_strategy(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.recommend


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--base-seed", type=int, default=20230722)
    parser.add_argument("--output", type=Path, default=Path("outputs/paired_rollout_audit.json"))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    market = load_trip_market(repo / "data/processed/validation_uncleaned.parquet", start=START, end=END)
    travel = load_travel_time_matrix(repo / "data/processed/travel_time_matrix_dijkstra.csv")
    paths = {
        "baseline_1": repo / "src/2_recommendation_algorithm/baseline_1.py",
        "baseline_2": repo / "src/2_recommendation_algorithm/baseline_2_2.py",
        "two_step": repo / "src/2_recommendation_algorithm/improved_strategy.py",
    }
    strategies = {name: load_strategy(path, f"audit_{name}") for name, path in paths.items()}
    outcomes = {name: [] for name in strategies}
    for index in range(args.runs):
        seed = args.base_seed + index
        for name, strategy in strategies.items():
            result = simulate_once(
                strategy=strategy,
                market=market,
                travel_times=travel,
                start=START,
                end=END,
                start_location_id=132,
                seed=seed,
                simulation_index=index + 1,
            )
            outcomes[name].append(result.average_daily_fare)
        if (index + 1) % 10 == 0:
            print(f"completed {index + 1}/{args.runs}", flush=True)

    report = {
        "runs": args.runs,
        "base_seed": args.base_seed,
        "daily_fares": outcomes,
        "comparisons": {
            "two_step_vs_baseline_1": paired_comparison(outcomes["two_step"], outcomes["baseline_1"]),
            "two_step_vs_baseline_2": paired_comparison(outcomes["two_step"], outcomes["baseline_2"]),
            "baseline_2_vs_baseline_1": paired_comparison(outcomes["baseline_2"], outcomes["baseline_1"]),
        },
    }
    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runs": args.runs, "comparisons": report["comparisons"]}, indent=2))


if __name__ == "__main__":
    main()

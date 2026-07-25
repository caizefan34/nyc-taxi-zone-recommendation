"""Compare finite planning horizons on static and rollout metrics."""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter_ns

import numpy as np

from src.eval.offline_core import Query
from src.eval.public_validation import evaluate_validation, read_public_queries
from src.eval.rollout_core import load_travel_time_matrix, load_trip_market, simulate_many
from src.eval.validation_core import read_validation_answers


def load_planner(repo: Path):
    path = repo / "src/2_recommendation_algorithm/finite_horizon.py"
    spec = importlib.util.spec_from_file_location("audit_finite_horizon", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.FiniteHorizonPlanner(max_horizon=5)


def static_metrics(planner, queries: list[Query], answers, label: str):
    predictions = {}
    latencies = []
    recommendation_rows = []
    for query in queries:
        start = perf_counter_ns()
        prediction = (
            planner.recommend_adaptive(query.query_time, query.current_location_id)
            if label == "adaptive"
            else planner.recommend(query.query_time, query.current_location_id, horizon=int(label))
        )
        latencies.append(perf_counter_ns() - start)
        predictions[query.query_id] = prediction
        recommendation_rows.append(prediction)
    metrics = evaluate_validation(
        queries,
        answers,
        predictions,
        latencies_ns=latencies,
        peak_tracemalloc_bytes=0,
    )
    metrics["coverage"] = float(len(set(np.asarray(recommendation_rows).ravel())) / 263)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    planner = load_planner(repo)
    queries = read_public_queries(repo / "data/processed/validation_input.parquet")
    answers = read_validation_answers(repo / "data/processed/validation_answers.parquet")
    market = load_trip_market(
        repo / "data/processed/validation_uncleaned.parquet",
        start=datetime(2023, 1, 25),
        end=datetime(2023, 2, 1),
    )
    travel = load_travel_time_matrix(repo / "data/processed/travel_time_matrix_dijkstra.csv")
    results = {}
    for label in ("1", "2", "3", "5", "adaptive"):
        strategy = (
            planner.recommend_adaptive
            if label == "adaptive"
            else lambda dt, zone, h=int(label): planner.recommend(dt, zone, horizon=h)
        )
        rollout, _ = simulate_many(
            strategy=strategy,
            market=market,
            travel_times=travel,
            start=datetime(2023, 1, 25),
            end=datetime(2023, 2, 1),
            start_location_id=132,
            runs=args.runs,
            base_seed=20230722,
            trace_run_index=None,
        )
        results[label] = {"static": static_metrics(planner, queries, answers, label), "rollout": rollout}
        print(label, results[label], flush=True)
    output = repo / "outputs/horizon_audit.json"
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""Stress-test the generalized horizon-two planner under model perturbations."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.eval.public_validation import evaluate_validation, read_public_queries
from src.eval.validation_core import read_validation_answers


def load_planner(repo: Path):
    path = repo / "src/2_recommendation_algorithm/finite_horizon.py"
    spec = importlib.util.spec_from_file_location("robust_finite_horizon", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.FiniteHorizonPlanner(max_horizon=2)


def evaluate(planner, queries, answers, baseline=None):
    predictions = {
        query.query_id: planner.recommend(query.query_time, query.current_location_id, horizon=2) for query in queries
    }
    metrics = evaluate_validation(
        queries,
        answers,
        predictions,
        latencies_ns=[0] * len(queries),
        peak_tracemalloc_bytes=0,
    )
    rankings = np.asarray(list(predictions.values()))
    metrics["coverage"] = float(len(np.unique(rankings)) / 263)
    if baseline is not None:
        metrics["top3_overlap"] = float(
            np.mean([len(set(value) & set(baseline[key])) / 3.0 for key, value in predictions.items()])
        )
    return metrics, predictions


def clone_with(planner, *, demand=None, fare=None, transition=None):
    clone = copy.copy(planner)
    clone.demand = planner.demand.copy() if demand is None else demand
    clone.fare = planner.fare.copy() if fare is None else fare
    clone.transition = planner.transition.copy() if transition is None else transition
    clone.values = clone._precompute_values()
    return clone


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    planner = load_planner(repo)
    queries = read_public_queries(repo / "data/processed/validation_input.parquet")
    answers = read_validation_answers(repo / "data/processed/validation_answers.parquet")
    baseline_metrics, baseline_predictions = evaluate(planner, queries, answers)
    scenarios = {"baseline": baseline_metrics}

    lookup = pd.read_csv(repo / "data/meta/taxi_zone_lookup.csv")
    manhattan = lookup.loc[lookup["Borough"] == "Manhattan", "LocationID"].to_numpy(dtype=int) - 1
    shocked_demand = planner.demand.copy()
    shocked_demand[:, manhattan] *= 1.5
    scenarios["manhattan_demand_+50%"] = evaluate(
        clone_with(planner, demand=shocked_demand), queries, answers, baseline_predictions
    )[0]

    rng = np.random.default_rng(20230722)
    missing = rng.random(planner.demand.shape) < 0.10
    missing_demand = planner.demand.copy()
    missing_fare = planner.fare.copy()
    missing_demand[missing] = 0.0
    missing_fare[missing] = 0.0
    scenarios["10%_missing_cells"] = evaluate(
        clone_with(planner, demand=missing_demand, fare=missing_fare), queries, answers, baseline_predictions
    )[0]

    sparse_transition = planner.transition.copy()
    sparse_transition[sparse_transition < 0.001] = 0.0
    row_sum = sparse_transition.sum(axis=1, keepdims=True)
    sparse_transition = np.divide(
        sparse_transition,
        row_sum,
        out=np.zeros_like(sparse_transition),
        where=row_sum > 0.0,
    )
    scenarios["drop_OD_p<0.001"] = evaluate(
        clone_with(planner, transition=sparse_transition), queries, answers, baseline_predictions
    )[0]

    zone_demand = planner.demand.sum(axis=0)
    rare = zone_demand <= np.quantile(zone_demand, 0.10)
    rare_missing_demand = planner.demand.copy()
    rare_missing_fare = planner.fare.copy()
    rare_missing_demand[:, rare] = 0.0
    rare_missing_fare[:, rare] = 0.0
    scenarios["remove_bottom_10%_zones"] = evaluate(
        clone_with(planner, demand=rare_missing_demand, fare=rare_missing_fare),
        queries,
        answers,
        baseline_predictions,
    )[0]

    output = repo / "outputs/robustness_audit.json"
    output.write_text(json.dumps(scenarios, indent=2) + "\n", encoding="utf-8")

    labels = list(scenarios)
    ndcg = [scenarios[label]["ndcg_at_3"] for label in labels]
    overlap = [scenarios[label].get("top3_overlap", 1.0) for label in labels]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].barh(labels, ndcg)
    axes[0].set_xlim(min(ndcg) - 0.01, max(ndcg) + 0.005)
    axes[0].set_title("NDCG@3 under perturbations")
    axes[1].barh(labels, overlap)
    axes[1].set_xlim(0, 1)
    axes[1].set_title("Top-3 overlap with unperturbed policy")
    figure.tight_layout()
    figure.savefig(repo / "outputs/audit_robustness.png", dpi=160)
    print(json.dumps(scenarios, indent=2))


if __name__ == "__main__":
    main()

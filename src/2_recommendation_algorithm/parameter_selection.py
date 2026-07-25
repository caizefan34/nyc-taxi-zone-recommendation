"""Select Task C lambda/gamma on the public validation split."""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow.parquet as pq


LAMBDA_CANDIDATES = (0.5, 1.0, 2.0)
GAMMA_CANDIDATES = (0.25, 0.5, 0.75)


def _load_strategy(path: Path):
    spec = importlib.util.spec_from_file_location("task_c_parameter_strategy", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    spec.loader.exec_module(module)
    return module


def _read_queries(path: Path) -> list[tuple[int, int, datetime]]:
    rows = []
    for row in pq.read_table(path).to_pylist():
        rows.append(
            (
                int(row["query_id"]),
                int(row["current_location_id"]),
                row["query_time"],
            )
        )
    return rows


def _read_answers(path: Path) -> dict[int, np.ndarray]:
    return {
        int(row["query_id"]): np.asarray(row["reference_utility"], dtype=float)
        for row in pq.read_table(path).to_pylist()
    }


def _score(strategy, queries, answers) -> dict[str, float]:
    discounts = 1.0 / np.log2(np.arange(2, 5, dtype=float))
    zones = np.arange(strategy.ZONE_COUNT)
    ndcgs = []
    hits = []
    started = perf_counter()
    for query_id, location_id, query_time in queries:
        predicted = np.asarray(strategy.recommend(query_time, location_id)) - 1
        utility = np.maximum(np.nan_to_num(answers[query_id], nan=0.0), 0.0)
        ideal = np.lexsort((zones, -utility))[:3]
        ideal_dcg = float(np.dot(utility[ideal], discounts))
        dcg = float(np.dot(utility[predicted], discounts))
        ndcgs.append(0.0 if ideal_dcg == 0.0 else dcg / ideal_dcg)
        hits.append(float(ideal[0] in predicted))
    elapsed = perf_counter() - started
    return {
        "ndcg_at_3": float(np.mean(ndcgs)),
        "hit_at_3": float(np.mean(hits)),
        "average_recommend_time_ms": elapsed * 1000.0 / len(queries),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    strategy = _load_strategy(Path(__file__).with_name("improved_strategy.py"))
    queries = _read_queries(args.queries)
    answers = _read_answers(args.answers)
    results = []
    for lambda_value in LAMBDA_CANDIDATES:
        strategy.LAMBDA = lambda_value
        strategy.v1 = strategy._precompute_v1()
        strategy.success_future = strategy._build_success_future()
        for gamma_value in GAMMA_CANDIDATES:
            strategy.GAMMA = gamma_value
            metrics = _score(strategy, queries, answers)
            results.append(
                {
                    "lambda": lambda_value,
                    "gamma": gamma_value,
                    **metrics,
                }
            )
            print(json.dumps(results[-1], ensure_ascii=False))

    selected = max(
        results,
        key=lambda item: (
            item["ndcg_at_3"],
            item["hit_at_3"],
            -item["average_recommend_time_ms"],
        ),
    )
    output = {
        "selection_split": "public January validation",
        "selection_metric": "NDCG@3, then Hit@3, then latency",
        "lambda_candidates": list(LAMBDA_CANDIDATES),
        "gamma_candidates": list(GAMMA_CANDIDATES),
        "results": results,
        "selected": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

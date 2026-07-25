"""Public January-validation evaluator for student recommendation strategies."""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import sys
from time import perf_counter_ns
import tracemalloc
from types import ModuleType
from typing import Callable, Mapping, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from eval.offline_core import Query, ZONE_COUNT, validate_top3
from eval.validation_core import read_validation_answers


PREDICTION_COLUMNS = ("query_id", "rank_1", "rank_2", "rank_3", "latency_ns")
Strategy = Callable[[datetime, int], Sequence[int]]


def evaluate_validation(
    queries: Sequence[Query],
    answers: Mapping[int, np.ndarray],
    predictions: Mapping[int, Sequence[int]],
    *,
    latencies_ns: Sequence[int],
    peak_tracemalloc_bytes: int,
) -> dict[str, object]:
    """Score Top-3 predictions against public two-step reference utilities."""
    if not queries:
        raise ValueError("at least one query is required")
    query_ids = [query.query_id for query in queries]
    if len(set(query_ids)) != len(query_ids):
        raise ValueError("query IDs must be unique")
    expected_ids = set(query_ids)
    _require_exact_ids("answer", expected_ids, set(answers))
    _require_exact_ids("prediction", expected_ids, set(predictions))
    if len(latencies_ns) != len(queries):
        raise ValueError("latencies_ns must have one value per query")

    discounts = 1.0 / np.log2(np.arange(2, 5, dtype=float))
    zone_indices = np.arange(ZONE_COUNT)
    ndcgs: list[float] = []
    hits: list[float] = []
    top1_utilities: list[float] = []
    for query in queries:
        utility = np.asarray(answers[query.query_id], dtype=float)
        if utility.shape != (ZONE_COUNT,):
            raise ValueError("each answer must contain 263 utilities")
        utility = np.maximum(np.nan_to_num(utility, nan=0.0), 0.0)
        top3 = validate_top3(predictions[query.query_id])
        predicted = np.asarray(top3, dtype=int) - 1
        ideal = np.lexsort((zone_indices, -utility))[:3]
        dcg = float(np.dot(utility[predicted], discounts))
        ideal_dcg = float(np.dot(utility[ideal], discounts))
        ndcgs.append(0.0 if ideal_dcg == 0.0 else dcg / ideal_dcg)
        hits.append(float(int(ideal[0]) + 1 in top3))
        top1_utilities.append(float(utility[predicted[0]]))

    return {
        "query_count": len(queries),
        "ndcg_at_3": float(np.mean(ndcgs)),
        "hit_at_3": float(np.mean(hits)),
        "reference_two_step_utility_at_1": float(np.mean(top1_utilities)),
        "average_recommend_time_ms": float(np.mean(latencies_ns)) / 1_000_000.0,
        "peak_tracemalloc_bytes": int(peak_tracemalloc_bytes),
    }


def read_public_queries(path: Path) -> list[Query]:
    """Read the release query schema without depending on staff-only code."""
    table = pq.read_table(path)
    expected_columns = [
        "query_id",
        "current_location_id",
        "query_time",
        "weekday",
        "time_slot",
    ]
    if table.schema.names != expected_columns:
        raise ValueError(f"query file columns must be {tuple(expected_columns)}")
    queries: list[Query] = []
    query_ids: set[int] = set()
    for row in table.to_pylist():
        query_time = row["query_time"]
        if not isinstance(query_time, datetime):
            raise ValueError("query_time values must be datetimes")
        location_id = int(row["current_location_id"])
        expected_slot = query_time.hour * 2 + query_time.minute // 30
        if (
            int(row["weekday"]) != query_time.weekday()
            or int(row["time_slot"]) != expected_slot
        ):
            raise ValueError("weekday and time_slot must match query_time")
        if not 1 <= location_id <= ZONE_COUNT:
            raise ValueError("current_location_id values must be in 1..263")
        query_id = int(row["query_id"])
        if query_id in query_ids:
            raise ValueError("query IDs must be unique")
        query_ids.add(query_id)
        queries.append(Query(query_id, location_id, query_time))
    if not queries:
        raise ValueError("query file must not be empty")
    return queries


def collect_validation_predictions(
    strategy_path: Path,
    queries: Sequence[Query],
    output_path: Path,
) -> tuple[dict[int, tuple[int, int, int]], list[int], int]:
    """Run a strategy on all public queries and save a reusable prediction file."""
    strategy = _load_strategy(strategy_path)
    predictions: dict[int, tuple[int, int, int]] = {}
    latencies_ns: list[int] = []
    tracemalloc.start()
    try:
        for query in queries:
            started_ns = perf_counter_ns()
            prediction = validate_top3(
                strategy(query.query_time, query.current_location_id)
            )
            latencies_ns.append(perf_counter_ns() - started_ns)
            predictions[query.query_id] = prediction
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "query_id": pa.array(list(predictions), type=pa.int64()),
                "rank_1": pa.array([value[0] for value in predictions.values()], type=pa.int16()),
                "rank_2": pa.array([value[1] for value in predictions.values()], type=pa.int16()),
                "rank_3": pa.array([value[2] for value in predictions.values()], type=pa.int16()),
                "latency_ns": pa.array(latencies_ns, type=pa.int64()),
            }
        ),
        output_path,
        compression="zstd",
    )
    return predictions, latencies_ns, peak_bytes


def _load_strategy(strategy_path: Path) -> Strategy:
    if not strategy_path.is_file():
        raise FileNotFoundError(strategy_path)
    spec = importlib.util.spec_from_file_location("public_student_strategy", strategy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load strategy: {strategy_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return _find_recommend_function(module)


def _find_recommend_function(module: ModuleType) -> Strategy:
    recommend = getattr(module, "recommend", None)
    if not callable(recommend):
        raise AttributeError(
            "strategy must define recommend(current_datetime, current_location_id)"
        )
    return recommend


def _require_exact_ids(label: str, expected: set[int], actual: set[int]) -> None:
    missing = sorted(expected - actual)
    if missing:
        raise ValueError(f"missing {label} IDs: {missing[:5]}")
    unexpected = sorted(actual - expected)
    if unexpected:
        raise ValueError(f"unexpected {label} IDs: {unexpected[:5]}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    queries = read_public_queries(args.queries)
    answers = read_validation_answers(args.answers)
    predictions, latencies_ns, peak_bytes = collect_validation_predictions(
        args.strategy,
        queries,
        args.predictions,
    )
    result = evaluate_validation(
        queries,
        answers,
        predictions,
        latencies_ns=latencies_ns,
        peak_tracemalloc_bytes=peak_bytes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

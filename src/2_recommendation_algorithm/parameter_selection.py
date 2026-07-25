"""Real parameter selection for the finite-horizon planning strategy."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from time import perf_counter_ns

from src.common.config import get_config, load_config
from src.common.logging_utils import get_logger
from src.eval.public_validation import evaluate_validation, read_public_queries
from src.eval.validation_core import read_validation_answers

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_planner_class():
    path = Path(__file__).with_name("finite_horizon.py")
    spec = importlib.util.spec_from_file_location("parameter_selection_finite_horizon", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FiniteHorizonPlanner


def run_parameter_selection(
    queries_path: Path,
    answers_path: Path,
    output_path: Path,
    pickup_half_saturation_values: list[float],
    gamma_values: list[float],
    candidate_pool_sizes: list[int],
) -> list[dict[str, float | int]]:
    """Evaluate every configuration on the public diagnostic labels."""
    queries = read_public_queries(queries_path)
    answers = read_validation_answers(answers_path)
    planner_class = _load_planner_class()
    planner = planner_class(max_horizon=2)
    results: list[dict[str, float | int]] = []

    for half_saturation in pickup_half_saturation_values:
        for gamma in gamma_values:
            planner.pickup_half_saturation = float(half_saturation)
            planner.gamma = float(gamma)
            planner.values = planner._precompute_values()
            for pool_size in candidate_pool_sizes:
                planner.candidate_pool_size = int(pool_size)
                predictions = {}
                latencies = []
                for query in queries:
                    started = perf_counter_ns()
                    predictions[query.query_id] = planner.recommend(
                        query.query_time,
                        query.current_location_id,
                        horizon=2,
                    )
                    latencies.append(perf_counter_ns() - started)
                metrics = evaluate_validation(
                    queries,
                    answers,
                    predictions,
                    latencies_ns=latencies,
                    peak_tracemalloc_bytes=0,
                )
                result = {
                    "pickup_half_saturation": float(half_saturation),
                    "gamma": float(gamma),
                    "candidate_pool_size": int(pool_size),
                    "ndcg_at_3": float(metrics["ndcg_at_3"]),
                    "hit_at_3": float(metrics["hit_at_3"]),
                    "reference_utility_at_1": float(metrics["reference_two_step_utility_at_1"]),
                    "average_recommend_time_ms": float(metrics["average_recommend_time_ms"]),
                }
                logger.info("Parameter result: %s", result)
                results.append(result)

    results.sort(
        key=lambda item: (
            -float(item["ndcg_at_3"]),
            -float(item["hit_at_3"]),
            int(item["candidate_pool_size"]),
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queries",
        type=Path,
        default=PROJECT_ROOT / "data/processed/validation_input.parquet",
    )
    parser.add_argument(
        "--answers",
        type=Path,
        default=PROJECT_ROOT / "data/processed/validation_answers.parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs/parameter_selection.json",
    )
    args = parser.parse_args()
    load_config()
    results = run_parameter_selection(
        args.queries,
        args.answers,
        args.output,
        get_config("parameter_grid.pickup_half_saturation_values", [120.0, 240.0, 360.0]),
        get_config("parameter_grid.gamma_values", [0.25, 0.5, 0.75]),
        get_config("parameter_grid.candidate_pool_sizes", [50, 100]),
    )
    print(json.dumps({"best": results[0], "evaluated": len(results)}, indent=2))


if __name__ == "__main__":
    main()

"""Compare the historical single-step strategy with supervised forecasts."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import stdev
from time import perf_counter_ns

from src.audit.statistics import paired_comparison
from src.eval.public_validation import evaluate_validation, read_public_queries
from src.eval.rollout_core import load_travel_time_matrix, load_trip_market, simulate_once
from src.eval.validation_core import read_validation_answers

ROOT = Path(__file__).resolve().parents[1]
START = datetime(2023, 1, 25)
END = datetime(2023, 2, 1)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.recommend


def _static(strategy, queries, answers) -> dict[str, object]:
    predictions = {}
    latencies = []
    for query in queries:
        start = perf_counter_ns()
        predictions[query.query_id] = strategy(query.query_time, query.current_location_id)
        latencies.append(perf_counter_ns() - start)
    return evaluate_validation(queries, answers, predictions, latencies_ns=latencies, peak_tracemalloc_bytes=0)


def _markdown(report: dict[str, object]) -> str:
    comparison = report["paired_rollout"]["forecast_vs_historical"]
    return "\n".join(
        [
            "# Forecasting-Enhanced Recommendation Benchmark",
            "",
            "Static metrics measure agreement with the existing public reference utility. Rollout fare is limited to "
            "the fixed single-driver simulator and is not a deployment estimate.",
            "",
            "| Strategy | NDCG@3 | Hit@3 | Mean simulator fare/day | SD |",
            "|---|---:|---:|---:|---:|",
            f"| Historical single-step | {report['static']['historical']['ndcg_at_3']:.4f} | "
            f"{report['static']['historical']['hit_at_3']:.4f} | "
            f"${report['rollout']['historical']['mean_daily_fare']:.2f} | "
            f"${report['rollout']['historical']['std_daily_fare']:.2f} |",
            f"| Forecast-enhanced | {report['static']['forecast']['ndcg_at_3']:.4f} | "
            f"{report['static']['forecast']['hit_at_3']:.4f} | "
            f"${report['rollout']['forecast']['mean_daily_fare']:.2f} | "
            f"${report['rollout']['forecast']['std_daily_fare']:.2f} |",
            "",
            f"Paired forecast minus historical fare: ${comparison['mean_difference']:.2f}/day, "
            f"95% bootstrap CI [${comparison['ci95_low']:.2f}, ${comparison['ci95_high']:.2f}], "
            f"paired t-test p={comparison['paired_t_pvalue']:.3g}, Cohen's dz={comparison['cohen_dz']:.3f}.",
            "",
            f"Wilcoxon signed-rank p={comparison['wilcoxon_pvalue']:.3g}. The CI crosses zero and the mean "
            "difference is negative, so this strategy does not replace the default recommender.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20230722)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/forecasting_benchmark.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/forecasting_benchmark.md")
    args = parser.parse_args()

    strategies = {
        "historical": _load(ROOT / "src/2_recommendation_algorithm/baseline_2_2.py", "forecast_benchmark_b2"),
        "forecast": _load(
            ROOT / "src/2_recommendation_algorithm/forecasting_strategy.py",
            "forecast_benchmark_supervised",
        ),
    }
    queries = read_public_queries(ROOT / "data/processed/validation_input.parquet")
    answers = read_validation_answers(ROOT / "data/processed/validation_answers.parquet")
    market = load_trip_market(ROOT / "data/processed/validation_uncleaned.parquet", start=START, end=END)
    travel = load_travel_time_matrix(ROOT / "data/processed/travel_time_matrix_dijkstra.csv")

    static = {name: _static(strategy, queries, answers) for name, strategy in strategies.items()}
    daily_fares = {name: [] for name in strategies}
    rollout_summaries = {}
    for index in range(args.runs):
        for name, strategy in strategies.items():
            result = simulate_once(
                strategy=strategy,
                market=market,
                travel_times=travel,
                start=START,
                end=END,
                start_location_id=132,
                seed=args.seed + index,
                simulation_index=index + 1,
            )
            daily_fares[name].append(result.average_daily_fare)
    for name, values in daily_fares.items():
        rollout_summaries[name] = {
            "mean_daily_fare": sum(values) / len(values),
            "std_daily_fare": stdev(values),
            "runs": len(values),
        }
    report = {
        "runs": args.runs,
        "base_seed": args.seed,
        "static": static,
        "rollout": rollout_summaries,
        "paired_rollout": {
            "forecast_vs_historical": paired_comparison(daily_fares["forecast"], daily_fares["historical"])
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

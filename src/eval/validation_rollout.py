"""Run a public January validation rollout for one student strategy."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence

from src.eval.rollout_core import (
    Strategy,
    load_travel_time_matrix,
    load_trip_market,
    simulate_many,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_START = datetime(2023, 1, 25, 0, 0)
VALIDATION_END = datetime(2023, 2, 1, 0, 0)
DEFAULT_START_LOCATION_ID = 132
DEFAULT_RUNS = 100
DEFAULT_BASE_SEED = 20230722
DEFAULT_MARKET_PATH = PROJECT_ROOT / "data/processed/validation_uncleaned.parquet"
DEFAULT_TRAVEL_TIMES_PATH = (
    PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"
)
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs/validation_rollout.json"
DEFAULT_TRACE_PATH = PROJECT_ROOT / "outputs/validation_trace.csv"
TRACE_FIELDNAMES = [
    "simulation_index",
    "decision_index",
    "decision_time",
    "origin_zone",
    "rank_1",
    "rank_2",
    "rank_3",
    "selected_rank",
    "selected_zone",
    "relocation_minutes",
    "relocation_slots",
    "pickup_attempt_time",
    "demand",
    "pickup_probability",
    "pickup_success",
    "trip_fare",
    "trip_dropoff_zone",
    "next_time",
    "next_zone",
    "event_result",
]


def evaluate_validation_rollout(
    *,
    strategy_path: Path,
    market_path: Path = DEFAULT_MARKET_PATH,
    travel_times_path: Path = DEFAULT_TRAVEL_TIMES_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    trace_path: Optional[Path] = DEFAULT_TRACE_PATH,
    runs: int = DEFAULT_RUNS,
    base_seed: int = DEFAULT_BASE_SEED,
    trace_run_index: Optional[int] = 1,
    start: datetime = VALIDATION_START,
    end: datetime = VALIDATION_END,
    start_location_id: int = DEFAULT_START_LOCATION_ID,
) -> Dict[str, object]:
    """Evaluate one strategy with a fixed public validation simulation."""
    if (trace_path is None) != (trace_run_index is None):
        raise ValueError("trace_path and trace_run_index must be provided together")
    strategy = _load_strategy(strategy_path)
    market = load_trip_market(market_path, start=start, end=end)
    travel_times = load_travel_time_matrix(travel_times_path)
    metrics, trace_rows = simulate_many(
        strategy=strategy,
        market=market,
        travel_times=travel_times,
        start=start,
        end=end,
        start_location_id=start_location_id,
        runs=runs,
        base_seed=base_seed,
        trace_run_index=trace_run_index,
    )
    result = dict(metrics)
    result.update(
        {
            "market_file": str(market_path),
            "travel_times_file": str(travel_times_path),
            "validation_start": start.isoformat(sep=" "),
            "validation_end": end.isoformat(sep=" "),
            "start_location_id": start_location_id,
            "trace_file": None if trace_path is None else str(trace_path),
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if trace_path is not None:
        _write_trace(trace_path, trace_rows)
    return result


def _load_strategy(strategy_path: Path) -> Strategy:
    if not strategy_path.is_file():
        raise FileNotFoundError(strategy_path)
    spec = importlib.util.spec_from_file_location("validation_rollout_strategy", strategy_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load strategy: {0}".format(strategy_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    recommend = getattr(module, "recommend", None)
    if not callable(recommend):
        raise AttributeError(
            "strategy must define recommend(current_datetime, current_location_id)"
        )
    return recommend


def _write_trace(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", type=Path, required=True)
    parser.add_argument("--market", type=Path, default=DEFAULT_MARKET_PATH)
    parser.add_argument("--travel-times", type=Path, default=DEFAULT_TRAVEL_TIMES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--trace-run", type=int, default=1)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    trace_path = None if args.trace_run == 0 else args.trace
    trace_run_index = None if args.trace_run == 0 else args.trace_run
    result = evaluate_validation_rollout(
        strategy_path=args.strategy,
        market_path=args.market,
        travel_times_path=args.travel_times,
        output_path=args.output,
        trace_path=trace_path,
        runs=args.runs,
        base_seed=args.seed,
        trace_run_index=trace_run_index,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

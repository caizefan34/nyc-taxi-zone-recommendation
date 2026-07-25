"""Deterministic public checks for required taxi-project artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Sequence, Tuple

import pyarrow.parquet as pq

from eval.offline_core import SLOT_COUNT, ZONE_COUNT, validate_top3
from eval.rollout_core import load_travel_time_matrix

REQUIRED_CLEANED_COLUMNS = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "weekday",
    "time_slot",
    "trip_duration",
}
REQUIRED_STATISTIC_COLUMNS = {
    "pickup_location_id",
    "weekday",
    "time_slot",
    "pickup_count",
    "mean_fare_amount",
}
CHECK_STATES = (
    (datetime(2023, 1, 29, 23, 45), 132),
    (datetime(2023, 1, 30, 8, 15), 132),
)


def run_sanity_checks(
    *,
    train_cleaned: Path,
    validation_cleaned: Path,
    statistics: Path,
    travel_times: Path,
    baseline_1: Path,
    baseline_2: Path,
    strategy: Path,
) -> Dict[str, object]:
    """Return a machine-readable report for artifacts and three strategies."""
    checks: Dict[str, Dict[str, object]] = {}
    artifact_ok, artifact_reason = _check_artifact_schemas(
        train_cleaned, validation_cleaned, statistics
    )
    checks["artifact_schema"] = _check_result(artifact_ok, artifact_reason)

    matrix, matrix_reason = _read_and_check_matrix(travel_times, train_cleaned)
    checks["travel_time_matrix"] = _check_result(
        matrix is not None,
        matrix_reason,
    )

    strategy_modules, interface_reason = _load_and_check_strategies(
        {
            "baseline_1": baseline_1,
            "baseline_2": baseline_2,
            "strategy": strategy,
        }
    )
    checks["strategy_interface"] = _check_result(
        strategy_modules is not None,
        interface_reason,
    )

    if artifact_ok and matrix is not None and strategy_modules is not None:
        demand, fare = _load_statistics(statistics)
        checks["baseline_1_reference"] = _check_baseline_1(
            strategy_modules["baseline_1"], demand
        )
        checks["baseline_2_reference"] = _check_baseline_2(
            strategy_modules["baseline_2"], demand, fare, matrix
        )
    else:
        reason = "requires valid artifacts, matrix, and strategy interface"
        checks["baseline_1_reference"] = _check_result(False, reason)
        checks["baseline_2_reference"] = _check_result(False, reason)

    return {
        "passed": all(bool(item["passed"]) for item in checks.values()),
        "checks": checks,
    }


def _check_artifact_schemas(
    train_cleaned: Path,
    validation_cleaned: Path,
    statistics: Path,
) -> Tuple[bool, str]:
    for label, path, expected in (
        ("train_cleaned", train_cleaned, REQUIRED_CLEANED_COLUMNS),
        ("validation_cleaned", validation_cleaned, REQUIRED_CLEANED_COLUMNS),
        ("zone_time_statistics", statistics, REQUIRED_STATISTIC_COLUMNS),
    ):
        try:
            columns = set(pq.read_schema(path).names)
        except Exception as error:
            return False, "{0}: cannot read schema ({1})".format(label, error)
        missing = sorted(expected.difference(columns))
        if missing:
            return False, "{0}: missing columns {1}".format(label, ", ".join(missing))
    return True, "all required schemas are present"


def _read_and_check_matrix(path: Path, train_cleaned: Path) -> Tuple[object, str]:
    try:
        matrix = load_travel_time_matrix(path)
    except Exception as error:
        return None, "travel_time_matrix: {0}".format(error)
    try:
        expected_diagonal = _same_zone_mean_durations(train_cleaned)
    except Exception as error:
        return None, "train_cleaned diagonal statistics: {0}".format(error)
    for index, row in enumerate(matrix, start=1):
        actual = float(row[index - 1])
        expected = expected_diagonal[index - 1]
        if not math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-5):
            return None, (
                "travel_time_matrix: diagonal at LocationID {0} must be {1:.6f}, "
                "got {2:.6f}"
            ).format(index, expected, actual)
        if any(
            (not math.isfinite(value) and value != float("inf")) or value < 0.0
            for value in row
        ):
            return None, "travel_time_matrix: values must be non-negative or inf"
    return matrix, (
        "matrix is 263 by 263 and its diagonal matches same-zone training trips"
    )


def _same_zone_mean_durations(path: Path) -> List[float]:
    sums = [0.0] * ZONE_COUNT
    counts = [0] * ZONE_COUNT
    table = pq.read_table(
        path,
        columns=["PULocationID", "DOLocationID", "trip_duration"],
    )
    for row in table.to_pylist():
        try:
            pickup = int(row["PULocationID"])
            dropoff = int(row["DOLocationID"])
            duration = float(row["trip_duration"])
        except (TypeError, ValueError):
            continue
        if (
            pickup == dropoff
            and 1 <= pickup <= ZONE_COUNT
            and math.isfinite(duration)
            and duration > 0.0
        ):
            sums[pickup - 1] += duration
            counts[pickup - 1] += 1
    return [
        sums[index] / counts[index] if counts[index] else 10.0
        for index in range(ZONE_COUNT)
    ]


def _load_and_check_strategies(
    paths: Dict[str, Path],
) -> Tuple[object, str]:
    modules: Dict[str, ModuleType] = {}
    for label, path in paths.items():
        try:
            module = _load_module(path, "sanity_{0}".format(label))
            recommend = getattr(module, "recommend", None)
            if not callable(recommend):
                return None, "{0}: missing recommend function".format(label)
            for current_time, current_zone in CHECK_STATES:
                validate_top3(recommend(current_time, current_zone))
        except Exception as error:
            return None, "{0}: {1}".format(label, error)
        modules[label] = module
    return modules, "all strategies return legal Top-3 recommendations"


def _check_baseline_1(module: ModuleType, demand: List[List[List[float]]]) -> Dict[str, object]:
    recommend = module.recommend
    for current_time, current_zone in CHECK_STATES:
        target_time = _next_half_hour(current_time)
        expected = _top3(demand[target_time.weekday()][_slot(target_time)])
        actual = validate_top3(recommend(current_time, current_zone))
        if actual != expected:
            return _check_result(
                False,
                "baseline_1: expected {0}, got {1} at {2}".format(
                    list(expected), list(actual), current_time.isoformat(sep=" ")
                ),
            )
    return _check_result(True, "matches pickup-count reference on fixed states")


def _check_baseline_2(
    module: ModuleType,
    demand: List[List[List[float]]],
    fare: List[List[List[float]]],
    matrix: Sequence[Sequence[float]],
) -> Dict[str, object]:
    recommend = module.recommend
    for current_time, current_zone in CHECK_STATES:
        target_time = _next_half_hour(current_time)
        weekday = target_time.weekday()
        slot = _slot(target_time)
        scores: List[float] = []
        for zone_index, travel_time in enumerate(matrix[current_zone - 1]):
            if math.isfinite(travel_time):
                scores.append(
                    demand[weekday][slot][zone_index]
                    * fare[weekday][slot][zone_index]
                    / (travel_time + 1.0)
                )
            else:
                scores.append(0.0)
        expected = _top3(scores)
        actual = validate_top3(recommend(current_time, current_zone))
        if actual != expected:
            return _check_result(
                False,
                "baseline_2: expected {0}, got {1} at {2}".format(
                    list(expected), list(actual), current_time.isoformat(sep=" ")
                ),
            )
    return _check_result(True, "matches joint-utility reference on fixed states")


def _load_statistics(path: Path) -> Tuple[List[List[List[float]]], List[List[List[float]]]]:
    demand = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    fare = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    table = pq.read_table(
        path,
        columns=[
            "pickup_location_id",
            "weekday",
            "time_slot",
            "pickup_count",
            "mean_fare_amount",
        ],
    )
    for row in table.to_pylist():
        location_id = int(row["pickup_location_id"])
        weekday = int(row["weekday"])
        slot = int(row["time_slot"])
        if not (1 <= location_id <= ZONE_COUNT and 0 <= weekday < 7 and 0 <= slot < SLOT_COUNT):
            continue
        index = location_id - 1
        demand[weekday][slot][index] = max(0.0, float(row["pickup_count"] or 0.0))
        raw_fare = row["mean_fare_amount"]
        if raw_fare is not None and math.isfinite(float(raw_fare)):
            fare[weekday][slot][index] = max(0.0, float(raw_fare))
    return demand, fare


def _top3(scores: Sequence[float]) -> Tuple[int, int, int]:
    ordered = sorted(range(1, ZONE_COUNT + 1), key=lambda zone: (-scores[zone - 1], zone))
    return tuple(ordered[:3])  # type: ignore[return-value]


def _next_half_hour(value: datetime) -> datetime:
    slot_start = value.replace(
        minute=(value.minute // 30) * 30,
        second=0,
        microsecond=0,
    )
    return slot_start + timedelta(minutes=30)


def _slot(value: datetime) -> int:
    return value.hour * 2 + value.minute // 30


def _load_module(path: Path, module_name: str) -> ModuleType:
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load strategy: {0}".format(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _check_result(passed: bool, reason: str) -> Dict[str, object]:
    return {"passed": passed, "reason": reason}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-cleaned", type=Path, required=True)
    parser.add_argument("--validation-cleaned", type=Path, required=True)
    parser.add_argument("--statistics", type=Path, required=True)
    parser.add_argument("--travel-times", type=Path, required=True)
    parser.add_argument("--baseline-1", type=Path, required=True)
    parser.add_argument("--baseline-2", type=Path, required=True)
    parser.add_argument("--strategy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    report = run_sanity_checks(
        train_cleaned=args.train_cleaned,
        validation_cleaned=args.validation_cleaned,
        statistics=args.statistics,
        travel_times=args.travel_times,
        baseline_1=args.baseline_1,
        baseline_2=args.baseline_2,
        strategy=args.strategy,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

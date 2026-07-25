"""Baseline 2 strategy using demand, fare, and precomputed travel times."""
from __future__ import annotations
import csv
from datetime import datetime, timedelta
import math
from pathlib import Path
import pyarrow.parquet as pq

ZONE_COUNT = 263
SMOOTHING = 1.0
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATISTICS_PATH = PROJECT_ROOT / "data/processed/zone_time_statistics.parquet"
TRAVEL_TIME_PATH = PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"


def recommend(
    current_datetime: datetime,
    current_location_id: int,
) -> list[int]:
    """Return the Top-3 LocationIDs for one simulator state."""
    if not isinstance(current_datetime, datetime):
        raise TypeError("current_datetime must be a datetime")
    if not 1 <= current_location_id <= ZONE_COUNT:
        raise ValueError("current_location_id must be in 1..263")

    target_time = _next_half_hour(current_datetime)
    slot = target_time.hour * 2 + target_time.minute // 30
    weekday = target_time.weekday()
    times = travel_time[current_location_id - 1]

    # Compute utility for each destination j
    scores = []
    for j in range(ZONE_COUNT):
        if math.isfinite(times[j]):
            demand_j = demand[weekday][slot][j]
            fare_j = mean_fare[weekday][slot][j]
            travel_cost = times[j] + SMOOTHING
            utility = demand_j * fare_j / travel_cost
            scores.append(utility)
        else:
            scores.append(0.0)

    # Top-3 selection: descending score, break ties by smaller LocationID
    ordered = sorted(
        range(1, ZONE_COUNT + 1),
        key=lambda zone: (-scores[zone - 1], zone),
    )
    return ordered[:3]


def _load_zone_statistics() -> tuple[list[list[list[float]]], list[list[list[float]]]]:
    demand = [[[0.0] * ZONE_COUNT for _ in range(48)] for _ in range(7)]
    mean_fare = [[[0.0] * ZONE_COUNT for _ in range(48)] for _ in range(7)]
    columns = [
        "pickup_location_id",
        "weekday",
        "time_slot",
        "pickup_count",
        "mean_fare_amount",
    ]
    for row in pq.read_table(STATISTICS_PATH, columns=columns).to_pylist():
        location_id = int(row["pickup_location_id"])
        weekday = int(row["weekday"])
        time_slot = int(row["time_slot"])
        if not 1 <= location_id <= ZONE_COUNT:
            continue
        index = location_id - 1
        demand[weekday][time_slot][index] = float(row["pickup_count"])
        raw_fare = row["mean_fare_amount"]
        if raw_fare is not None and math.isfinite(float(raw_fare)):
            mean_fare[weekday][time_slot][index] = max(0.0, float(raw_fare))
    return demand, mean_fare


def _load_travel_time_matrix() -> list[list[float]]:
    with TRAVEL_TIME_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if len(header) != ZONE_COUNT + 1:
            raise ValueError("travel-time matrix must have 263 destination columns")
        matrix = []
        for expected_origin, row in enumerate(reader, start=1):
            if int(row[0]) != expected_origin or len(row) != ZONE_COUNT + 1:
                raise ValueError("invalid travel-time matrix row")
            matrix.append([float(value) for value in row[1:]])
    if len(matrix) != ZONE_COUNT:
        raise ValueError("travel-time matrix must have 263 origin rows")
    return matrix


def _next_half_hour(value: datetime) -> datetime:
    slot_start = value.replace(
        minute=(value.minute // 30) * 30,
        second=0,
        microsecond=0,
    )
    return slot_start + timedelta(minutes=30)


# Read the statistics and time matrix once when the strategy file is loaded.
demand, mean_fare = _load_zone_statistics()
travel_time = _load_travel_time_matrix()

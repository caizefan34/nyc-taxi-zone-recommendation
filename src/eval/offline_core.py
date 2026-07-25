"""Pure helpers for the staff-only offline recommendation evaluator."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import random
from typing import Sequence

import numpy as np
import pyarrow.parquet as pq


ZONE_COUNT = 263
SLOT_COUNT = 48
WEEK_SLOT_COUNT = 7 * SLOT_COUNT
SLOT_MINUTES = 30
# This helper scores demand aggregated from one concrete validation-market
# week/date cell.  Task C's multi-week training statistic uses 240 instead.
DEMAND_HALF_SATURATION = 40.0


@dataclass(frozen=True)
class Query:
    """One unlabeled recommendation state used by the offline evaluator."""

    query_id: int
    current_location_id: int
    query_time: datetime


def slot_start(value: datetime) -> datetime:
    """Return the start of the 30-minute slot containing ``value``."""
    return value.replace(
        minute=(value.minute // 30) * 30,
        second=0,
        microsecond=0,
    )


def minutes_to_slots(minutes: np.ndarray) -> np.ndarray:
    """Round minutes to 30-minute slots with ``floor(x + 0.5)``."""
    return np.floor(minutes / SLOT_MINUTES + 0.5).astype(np.int64)


def validate_top3(values: Sequence[int]) -> tuple[int, int, int]:
    """Validate and normalize one ranked Top-3 recommendation."""
    top3 = tuple(int(value) for value in values)
    if len(top3) != 3 or len(set(top3)) != 3:
        raise ValueError("recommendation must contain three distinct zones")
    if not all(1 <= zone <= ZONE_COUNT for zone in top3):
        raise ValueError("recommended zones must be in 1..263")
    return top3  # type: ignore[return-value]


def build_utility(
    origin_location_id: int,
    current_datetime: datetime,
    demand: Sequence[Sequence[Sequence[float]]],
    fare: Sequence[Sequence[Sequence[float]]],
    travel_times: Sequence[Sequence[float]],
) -> np.ndarray:
    """Return the 263 hidden utilities for one current state.

    Each destination uses the market at its actual rounded arrival slot.  The
    current zone has zero empty-relocation time even though the matrix diagonal
    stores historical same-zone trip duration.  A non-finite or negative travel
    time represents an unreachable destination and receives zero utility.
    """
    if not 1 <= origin_location_id <= ZONE_COUNT:
        raise ValueError("origin_location_id must be in 1..263")

    demand_array = np.asarray(demand, dtype=float)
    fare_array = np.asarray(fare, dtype=float)
    times = np.asarray(travel_times, dtype=float)[origin_location_id - 1]
    if demand_array.shape != (7, SLOT_COUNT, ZONE_COUNT):
        raise ValueError("demand and fare must have shape (7, 48, 263)")
    if fare_array.shape != (7, SLOT_COUNT, ZONE_COUNT):
        raise ValueError("demand and fare must have shape (7, 48, 263)")
    if times.shape != (ZONE_COUNT,):
        raise ValueError("travel_times must have shape (263, 263)")

    utility = np.zeros(ZONE_COUNT, dtype=float)
    reachable = np.isfinite(times) & (times >= 0.0)
    movement_slots = np.zeros(ZONE_COUNT, dtype=np.int64)
    non_stay = np.arange(ZONE_COUNT) != origin_location_id - 1
    movable = reachable & non_stay
    movement_slots[movable] = minutes_to_slots(times[movable])
    state = (
        current_datetime.weekday() * SLOT_COUNT
        + current_datetime.hour * 2
        + current_datetime.minute // SLOT_MINUTES
    )
    arrivals = (state + movement_slots) % WEEK_SLOT_COUNT
    destinations = np.arange(ZONE_COUNT)
    flat_demand = demand_array.reshape(WEEK_SLOT_COUNT, ZONE_COUNT)
    flat_fare = fare_array.reshape(WEEK_SLOT_COUNT, ZONE_COUNT)
    demand_values = flat_demand[arrivals, destinations]
    fare_values = flat_fare[arrivals, destinations]
    pickup_probability = demand_values / (
        demand_values + DEMAND_HALF_SATURATION
    )
    utility[reachable] = (
        pickup_probability[reachable]
        * fare_values[reachable]
        / (movement_slots[reachable] + 1.0)
    )
    utility[~np.isfinite(utility)] = 0.0
    return np.maximum(utility, 0.0)


def load_travel_time_matrix(path: Path) -> np.ndarray:
    """Load one directed 263-by-263 CSV travel-time matrix."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or len(header) != ZONE_COUNT + 1:
            raise ValueError("travel-time matrix must have 263 destination columns")
        rows: list[list[float]] = []
        for expected_origin, row in enumerate(reader, start=1):
            if len(row) != ZONE_COUNT + 1 or int(row[0]) != expected_origin:
                raise ValueError("invalid travel-time matrix row")
            rows.append([float(value) for value in row[1:]])
    if len(rows) != ZONE_COUNT:
        raise ValueError("travel-time matrix must have 263 origin rows")
    return np.asarray(rows, dtype=float)


def aggregate_market(
    trips_path: Path,
    start: datetime,
    end: datetime,
) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate valid test pickups into weekday-by-slot demand and fare arrays."""
    if end <= start:
        raise ValueError("end must be after start")

    demand = np.zeros((7, SLOT_COUNT, ZONE_COUNT), dtype=float)
    fare_sum = np.zeros_like(demand)
    parquet = pq.ParquetFile(trips_path)
    columns = ["tpep_pickup_datetime", "PULocationID", "fare_amount"]
    for batch in parquet.iter_batches(columns=columns, batch_size=65_536):
        pickup_times, pickup_zones, fares = (
            batch.column(column).to_pylist() for column in columns
        )
        for pickup_time, raw_zone, raw_fare in zip(
            pickup_times,
            pickup_zones,
            fares,
        ):
            if not isinstance(pickup_time, datetime) or not start <= pickup_time < end:
                continue
            if raw_zone is None or raw_fare is None:
                continue
            try:
                zone = int(raw_zone)
                fare = float(raw_fare)
            except (TypeError, ValueError):
                continue
            if not 1 <= zone <= ZONE_COUNT or not np.isfinite(fare) or fare < 0.0:
                continue
            weekday = pickup_time.weekday()
            slot = pickup_time.hour * 2 + pickup_time.minute // 30
            demand[weekday, slot, zone - 1] += 1.0
            fare_sum[weekday, slot, zone - 1] += fare

    mean_fare = np.divide(
        fare_sum,
        demand,
        out=np.zeros_like(fare_sum),
        where=demand > 0.0,
    )
    return demand, mean_fare


def eligible_query_states(
    demand: Sequence[Sequence[Sequence[float]]],
    fare: Sequence[Sequence[Sequence[float]]],
    travel_times: Sequence[Sequence[float]],
) -> np.ndarray:
    """Mark current states with at least one reachable positive-utility zone.

    The result is indexed by current weekday, current slot and origin index.
    Candidate demand is checked at its own rounded arrival slot.  This lets
    query sampling avoid constructing 263 utilities for every raw dropoff.
    """
    demand_values = np.asarray(demand, dtype=float)
    fare_values = np.asarray(fare, dtype=float)
    matrix = np.asarray(travel_times, dtype=float)
    if demand_values.shape != (7, SLOT_COUNT, ZONE_COUNT):
        raise ValueError("demand must have shape (7, 48, 263)")
    if fare_values.shape != (7, SLOT_COUNT, ZONE_COUNT):
        raise ValueError("fare must have shape (7, 48, 263)")
    if matrix.shape != (ZONE_COUNT, ZONE_COUNT):
        raise ValueError("travel_times must have shape (263, 263)")

    positive_market = (
        np.isfinite(demand_values)
        & np.isfinite(fare_values)
        & (demand_values > 0.0)
        & (fare_values > 0.0)
    )
    flat_market = positive_market.reshape(WEEK_SLOT_COUNT, ZONE_COUNT)
    eligible = np.zeros((WEEK_SLOT_COUNT, ZONE_COUNT), dtype=bool)
    destinations = np.arange(ZONE_COUNT)
    for origin in range(ZONE_COUNT):
        times = matrix[origin]
        reachable = np.isfinite(times) & (times >= 0.0)
        movement_slots = np.zeros(ZONE_COUNT, dtype=np.int64)
        movable = reachable & (destinations != origin)
        movement_slots[movable] = minutes_to_slots(times[movable])
        for state in range(WEEK_SLOT_COUNT):
            arrivals = (state + movement_slots) % WEEK_SLOT_COUNT
            eligible[state, origin] = bool(
                np.any(reachable & flat_market[arrivals, destinations])
            )
    return eligible.reshape(7, SLOT_COUNT, ZONE_COUNT)


def sample_queries(
    trips_path: Path,
    travel_path: Path,
    *,
    start: datetime,
    end: datetime,
    per_stratum: int,
    seed: int,
) -> list[dict[str, object]]:
    """Reservoir-sample valid unlabeled dropoff states per weekday and slot."""
    if per_stratum <= 0:
        raise ValueError("per_stratum must be positive")

    demand, fare = aggregate_market(trips_path, start, end)
    travel_times = load_travel_time_matrix(travel_path)
    eligible = eligible_query_states(demand, fare, travel_times)
    rng = random.Random(seed)
    seen: dict[tuple[int, int], int] = {}
    samples: dict[tuple[int, int], list[tuple[int, datetime]]] = {}
    parquet = pq.ParquetFile(trips_path)
    columns = ["tpep_dropoff_datetime", "DOLocationID"]
    for batch in parquet.iter_batches(columns=columns, batch_size=65_536):
        dropoff_times, dropoff_zones = (
            batch.column(column).to_pylist() for column in columns
        )
        for dropoff_time, raw_zone in zip(dropoff_times, dropoff_zones):
            if not isinstance(dropoff_time, datetime) or not start <= dropoff_time < end:
                continue
            if raw_zone is None:
                continue
            try:
                zone = int(raw_zone)
            except (TypeError, ValueError):
                continue
            if not 1 <= zone <= ZONE_COUNT:
                continue
            query_time = slot_start(dropoff_time)
            query_slot = query_time.hour * 2 + query_time.minute // 30
            if not eligible[query_time.weekday(), query_slot, zone - 1]:
                continue

            stratum = (
                query_time.weekday(),
                query_slot,
            )
            count = seen.get(stratum, 0) + 1
            seen[stratum] = count
            bucket = samples.setdefault(stratum, [])
            candidate = (zone, query_time)
            if len(bucket) < per_stratum:
                bucket.append(candidate)
            else:
                replacement = rng.randrange(count)
                if replacement < per_stratum:
                    bucket[replacement] = candidate

    rows: list[dict[str, object]] = []
    query_id = 1
    for stratum in sorted(samples):
        for zone, query_time in sorted(samples[stratum], key=lambda value: (value[1], value[0])):
            rows.append(
                {
                    "query_id": query_id,
                    "current_location_id": zone,
                    "query_time": query_time,
                }
            )
            query_id += 1
    return rows


def score_predictions(
    queries: Sequence[Query],
    predictions: dict[int, tuple[int, int, int]],
    demand: Sequence[Sequence[Sequence[float]]],
    fare: Sequence[Sequence[Sequence[float]]],
    travel_times: Sequence[Sequence[float]],
) -> dict[str, object]:
    """Calculate ranking, utility and relocation metrics for a prediction map."""
    query_ids = [query.query_id for query in queries]
    if len(set(query_ids)) != len(query_ids):
        raise ValueError("query IDs must be unique")
    expected_ids = set(query_ids)
    predicted_ids = set(predictions)
    missing = sorted(expected_ids - predicted_ids)
    if missing:
        raise ValueError(f"missing predictions for query IDs: {missing[:5]}")
    unexpected = sorted(predicted_ids - expected_ids)
    if unexpected:
        raise ValueError(f"unexpected predictions for query IDs: {unexpected[:5]}")
    if not queries:
        raise ValueError("at least one query is required")

    matrix = np.asarray(travel_times, dtype=float)
    discounts = 1.0 / np.log2(np.arange(2, 5, dtype=float))
    ndcgs: list[float] = []
    hits: list[float] = []
    realized_utilities: list[float] = []
    finite_relocation_times: list[float] = []
    unreachable_top1_count = 0
    zone_indices = np.arange(ZONE_COUNT)

    for query in queries:
        top3 = validate_top3(predictions[query.query_id])
        utility = build_utility(
            query.current_location_id,
            query.query_time,
            demand,
            fare,
            matrix,
        )
        ideal = np.lexsort((zone_indices, -utility))[:3]
        predicted_indices = np.asarray(top3, dtype=int) - 1
        dcg = float(np.dot(utility[predicted_indices], discounts))
        ideal_dcg = float(np.dot(utility[ideal], discounts))
        ndcgs.append(0.0 if ideal_dcg == 0.0 else dcg / ideal_dcg)
        hits.append(float(int(ideal[0]) + 1 in top3))
        realized_utilities.append(float(utility[predicted_indices[0]]))

        if int(predicted_indices[0]) + 1 == query.current_location_id:
            travel_time = 0.0
        else:
            travel_time = float(
                matrix[query.current_location_id - 1, predicted_indices[0]]
            )
        if np.isfinite(travel_time) and travel_time >= 0.0:
            finite_relocation_times.append(travel_time)
        else:
            unreachable_top1_count += 1

    return {
        "query_count": len(queries),
        "ndcg_at_3": float(np.mean(ndcgs)),
        "hit_at_3": float(np.mean(hits)),
        "realized_utility": float(np.mean(realized_utilities)),
        "average_relocation_time_minutes": (
            float(np.mean(finite_relocation_times))
            if finite_relocation_times
            else None
        ),
        "unreachable_top1_count": unreachable_top1_count,
        "unreachable_top1_rate": unreachable_top1_count / len(queries),
    }

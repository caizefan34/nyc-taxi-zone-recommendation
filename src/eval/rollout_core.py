"""Public stochastic rollout primitives for taxi recommendation strategies."""

from __future__ import annotations

import csv
import math
import random
import statistics
from array import array
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter_ns
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pyarrow.parquet as pq

from src.eval.offline_core import validate_top3

ZONE_COUNT = 263
SLOT_MINUTES = 30
TOP3_WEIGHTS = (0.6, 0.3, 0.1)
# Rollout cells belong to one concrete date.  Task C's multi-week training
# pickup_count uses the separate calibrated constant 240.
DEMAND_HALF_SATURATION = 40.0
MAX_TRIP_DURATION_MINUTES = 240.0
Strategy = Callable[[datetime, int], Sequence[int]]


class MarketCell:
    """Compact collection of validation trips in one day-slot-zone cell."""

    __slots__ = ("dropoff_zones", "fares", "duration_slots")

    def __init__(self) -> None:
        self.dropoff_zones = array("H")
        self.fares = array("f")
        self.duration_slots = array("B")

    def append(self, dropoff_zone: int, fare: float, duration_slots: int) -> None:
        self.dropoff_zones.append(dropoff_zone)
        self.fares.append(fare)
        self.duration_slots.append(duration_slots)

    def __len__(self) -> int:
        return len(self.dropoff_zones)


@dataclass(frozen=True)
class DestinationChoice:
    """The executable recommendation rank chosen for one decision."""

    zone: int
    rank: Optional[int]


@dataclass(frozen=True)
class SimulationResult:
    """One run's aggregate outcome."""

    total_fare: float
    average_daily_fare: float
    served_trips: int
    relocation_count: int
    relocation_minutes: float
    failed_pickup_attempts: int
    recommend_calls: int
    recommend_time_seconds: float


def minutes_to_slots(minutes: float) -> int:
    """Round non-negative minutes to the nearest half-hour slot.

    Values exactly halfway between two slots round upward.  The result may be
    zero because every pickup attempt separately consumes one full slot.
    """
    if not math.isfinite(minutes) or minutes < 0.0:
        raise ValueError("minutes must be a finite non-negative number")
    return math.floor(minutes / SLOT_MINUTES + 0.5)


def pickup_probability(demand: int) -> float:
    """Return the fixed concave pickup-success probability."""
    if demand < 0:
        raise ValueError("demand cannot be negative")
    return demand / (demand + DEMAND_HALF_SATURATION)


def load_trip_market(
    path: Path,
    *,
    start: datetime,
    end: datetime,
) -> Dict[int, MarketCell]:
    """Build an immutable simulation market from an uncleaned public table."""
    if start >= end:
        raise ValueError("start must be before end")
    columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
    ]
    market: Dict[int, MarketCell] = {}
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(columns=columns, batch_size=65_536):
        values = [batch.column(index).to_pylist() for index in range(len(columns))]
        for pickup_time, dropoff_time, raw_pickup, raw_dropoff, raw_fare in zip(
            *values
        ):
            if not isinstance(pickup_time, datetime) or not isinstance(
                dropoff_time, datetime
            ):
                continue
            if not (start <= pickup_time < end and pickup_time < dropoff_time <= end):
                continue
            try:
                pickup_zone = int(raw_pickup)
                dropoff_zone = int(raw_dropoff)
            except (TypeError, ValueError):
                continue
            if not (
                1 <= pickup_zone <= ZONE_COUNT
                and 1 <= dropoff_zone <= ZONE_COUNT
            ):
                continue
            duration_minutes = (dropoff_time - pickup_time).total_seconds() / 60.0
            if not 0.0 < duration_minutes <= MAX_TRIP_DURATION_MINUTES:
                continue
            try:
                fare = float(raw_fare)
            except (TypeError, ValueError):
                fare = 0.0
            if not math.isfinite(fare) or fare < 0.0:
                fare = 0.0
            key = _market_key(pickup_time, pickup_zone, start)
            cell = market.get(key)
            if cell is None:
                cell = MarketCell()
                market[key] = cell
            cell.append(dropoff_zone, fare, minutes_to_slots(duration_minutes))
    return market


def load_travel_time_matrix(path: Path) -> List[List[float]]:
    """Read a directed 263 by 263 CSV matrix written by Baseline 2.1."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError("travel-time matrix is empty") from error
        if len(header) != ZONE_COUNT + 1:
            raise ValueError("travel-time matrix must have 263 destination columns")
        matrix: List[List[float]] = []
        for expected_origin, row in enumerate(reader, start=1):
            if len(row) != ZONE_COUNT + 1 or int(row[0]) != expected_origin:
                raise ValueError("invalid travel-time matrix row")
            parsed: List[float] = []
            for raw_value in row[1:]:
                value = float(raw_value)
                if math.isnan(value) or value < 0.0:
                    raise ValueError("travel times must be non-negative numbers or inf")
                parsed.append(value)
            matrix.append(parsed)
    if len(matrix) != ZONE_COUNT:
        raise ValueError("travel-time matrix must have 263 origin rows")
    return matrix


def choose_destination(
    top3: Tuple[int, int, int],
    *,
    current_location_id: int,
    travel_times: Sequence[Sequence[float]],
    rng: random.Random,
) -> DestinationChoice:
    """Sample an executable Top-3 action after removing unreachable zones."""
    executable: List[Tuple[int, int, float]] = []
    for rank, (zone, weight) in enumerate(zip(top3, TOP3_WEIGHTS), start=1):
        if zone == current_location_id or math.isfinite(
            travel_times[current_location_id - 1][zone - 1]
        ):
            executable.append((zone, rank, weight))
    if not executable:
        return DestinationChoice(zone=current_location_id, rank=None)

    threshold = rng.random() * sum(weight for _, _, weight in executable)
    cumulative = 0.0
    for zone, rank, weight in executable:
        cumulative += weight
        if threshold < cumulative:
            return DestinationChoice(zone=zone, rank=rank)
    zone, rank, _ = executable[-1]
    return DestinationChoice(zone=zone, rank=rank)


def simulate_once(
    *,
    strategy: Strategy,
    market: Dict[int, MarketCell],
    travel_times: Sequence[Sequence[float]],
    start: datetime,
    end: datetime,
    start_location_id: int,
    seed: int,
    simulation_index: int,
    trace_rows: Optional[List[Dict[str, object]]] = None,
) -> SimulationResult:
    """Simulate one driver's decisions through the requested time window."""
    if not 1 <= start_location_id <= ZONE_COUNT:
        raise ValueError("start_location_id must be in 1..263")
    rng = random.Random(seed)
    current_time = start
    current_location_id = start_location_id
    total_fare = 0.0
    served_trips = 0
    relocation_count = 0
    relocation_minutes = 0.0
    failed_pickup_attempts = 0
    recommend_calls = 0
    recommend_time_seconds = 0.0
    decision_index = 0

    while current_time < end:
        decision_index += 1
        decision_time = current_time
        origin_zone = current_location_id
        recommend_started_ns = perf_counter_ns()
        top3 = validate_top3(strategy(decision_time, origin_zone))
        recommend_time_seconds += (perf_counter_ns() - recommend_started_ns) / 1e9
        recommend_calls += 1

        choice = choose_destination(
            top3,
            current_location_id=origin_zone,
            travel_times=travel_times,
            rng=rng,
        )
        selected_zone = choice.zone
        relocation_slots = 0
        relocation_minutes_raw = 0.0
        if selected_zone != origin_zone:
            relocation_minutes_raw = travel_times[origin_zone - 1][selected_zone - 1]
            relocation_slots = minutes_to_slots(relocation_minutes_raw)
            current_time += timedelta(minutes=relocation_slots * SLOT_MINUTES)
            current_location_id = selected_zone
            relocation_count += 1
            relocation_minutes += relocation_minutes_raw

        if current_time >= end:
            _append_trace(
                trace_rows,
                simulation_index=simulation_index,
                decision_index=decision_index,
                decision_time=decision_time,
                origin_zone=origin_zone,
                top3=top3,
                choice=choice,
                selected_zone=selected_zone,
                relocation_minutes=relocation_minutes_raw,
                relocation_slots=relocation_slots,
                pickup_attempt_time=None,
                demand=None,
                probability=None,
                pickup_success=None,
                trip_fare=None,
                trip_dropoff_zone=None,
                next_time=current_time,
                next_zone=current_location_id,
                event_result="simulation_ended_during_relocation",
            )
            break

        pickup_attempt_time = current_time
        cell = market.get(_market_key(pickup_attempt_time, current_location_id, start))
        demand = 0 if cell is None else len(cell)
        probability = pickup_probability(demand)
        pickup_success = cell is not None and rng.random() < probability
        current_time += timedelta(minutes=SLOT_MINUTES)

        trip_fare: Optional[float] = None
        trip_dropoff_zone: Optional[int] = None
        if pickup_success:
            assert cell is not None
            trip_index = rng.randrange(demand)
            trip_fare = float(cell.fares[trip_index])
            trip_dropoff_zone = int(cell.dropoff_zones[trip_index])
            current_time += timedelta(
                minutes=int(cell.duration_slots[trip_index]) * SLOT_MINUTES
            )
            current_location_id = trip_dropoff_zone
            total_fare += trip_fare
            served_trips += 1
            event_result = "served_trip"
        else:
            failed_pickup_attempts += 1
            event_result = "pickup_failed"

        _append_trace(
            trace_rows,
            simulation_index=simulation_index,
            decision_index=decision_index,
            decision_time=decision_time,
            origin_zone=origin_zone,
            top3=top3,
            choice=choice,
            selected_zone=selected_zone,
            relocation_minutes=relocation_minutes_raw,
            relocation_slots=relocation_slots,
            pickup_attempt_time=pickup_attempt_time,
            demand=demand,
            probability=probability,
            pickup_success=pickup_success,
            trip_fare=trip_fare,
            trip_dropoff_zone=trip_dropoff_zone,
            next_time=current_time,
            next_zone=current_location_id,
            event_result=event_result,
        )

    days = (end - start).total_seconds() / 86_400.0
    return SimulationResult(
        total_fare=total_fare,
        average_daily_fare=total_fare / days,
        served_trips=served_trips,
        relocation_count=relocation_count,
        relocation_minutes=relocation_minutes,
        failed_pickup_attempts=failed_pickup_attempts,
        recommend_calls=recommend_calls,
        recommend_time_seconds=recommend_time_seconds,
    )


def simulate_many(
    *,
    strategy: Strategy,
    market: Dict[int, MarketCell],
    travel_times: Sequence[Sequence[float]],
    start: datetime,
    end: datetime,
    start_location_id: int,
    runs: int,
    base_seed: int,
    trace_run_index: Optional[int] = None,
) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    """Run independent fixed-seed simulations and return aggregates and trace."""
    if runs <= 0:
        raise ValueError("runs must be positive")
    if trace_run_index is not None and not 1 <= trace_run_index <= runs:
        raise ValueError("trace_run_index must be in 1..runs")
    if start >= end:
        raise ValueError("start must be before end")

    results: List[SimulationResult] = []
    trace_rows: List[Dict[str, object]] = []
    for zero_based_index in range(runs):
        simulation_index = zero_based_index + 1
        results.append(
            simulate_once(
                strategy=strategy,
                market=market,
                travel_times=travel_times,
                start=start,
                end=end,
                start_location_id=start_location_id,
                seed=base_seed + zero_based_index,
                simulation_index=simulation_index,
                trace_rows=(
                    trace_rows if simulation_index == trace_run_index else None
                ),
            )
        )

    daily_fares = [result.average_daily_fare for result in results]
    recommend_calls = sum(result.recommend_calls for result in results)
    recommend_seconds = sum(result.recommend_time_seconds for result in results)
    return {
        "metric": "average_daily_fare",
        "runs": runs,
        "days_per_run": (end - start).total_seconds() / 86_400.0,
        "average_daily_fare": statistics.fmean(daily_fares),
        "daily_fare_stddev": statistics.pstdev(daily_fares),
        "average_served_trips": statistics.fmean(
            result.served_trips for result in results
        ),
        "average_relocations": statistics.fmean(
            result.relocation_count for result in results
        ),
        "average_relocation_minutes": statistics.fmean(
            result.relocation_minutes for result in results
        ),
        "average_recommend_time_ms": (
            recommend_seconds / recommend_calls * 1_000.0
            if recommend_calls
            else 0.0
        ),
        "recommend_calls": recommend_calls,
        "base_seed": base_seed,
        "top3_sampling_weights": list(TOP3_WEIGHTS),
        "first_run": asdict(results[0]),
    }, trace_rows


def _market_key(value: datetime, location_id: int, start: datetime) -> int:
    day_index = (value.date() - start.date()).days
    time_slot = value.hour * 2 + value.minute // 30
    return (day_index * 48 + time_slot) * ZONE_COUNT + location_id - 1


def _append_trace(
    trace_rows: Optional[List[Dict[str, object]]],
    *,
    simulation_index: int,
    decision_index: int,
    decision_time: datetime,
    origin_zone: int,
    top3: Tuple[int, int, int],
    choice: DestinationChoice,
    selected_zone: int,
    relocation_minutes: float,
    relocation_slots: int,
    pickup_attempt_time: Optional[datetime],
    demand: Optional[int],
    probability: Optional[float],
    pickup_success: Optional[bool],
    trip_fare: Optional[float],
    trip_dropoff_zone: Optional[int],
    next_time: datetime,
    next_zone: int,
    event_result: str,
) -> None:
    if trace_rows is None:
        return
    trace_rows.append(
        {
            "simulation_index": simulation_index,
            "decision_index": decision_index,
            "decision_time": _format_time(decision_time),
            "origin_zone": origin_zone,
            "rank_1": top3[0],
            "rank_2": top3[1],
            "rank_3": top3[2],
            "selected_rank": choice.rank,
            "selected_zone": selected_zone,
            "relocation_minutes": relocation_minutes,
            "relocation_slots": relocation_slots,
            "pickup_attempt_time": (
                None if pickup_attempt_time is None else _format_time(pickup_attempt_time)
            ),
            "demand": demand,
            "pickup_probability": probability,
            "pickup_success": pickup_success,
            "trip_fare": trip_fare,
            "trip_dropoff_zone": trip_dropoff_zone,
            "next_time": _format_time(next_time),
            "next_zone": next_zone,
            "event_result": event_result,
        }
    )


def _format_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")

"""Improved strategy: two-step finite horizon planning with transition probabilities."""
from __future__ import annotations
import csv
from datetime import datetime, timedelta
import math
from pathlib import Path
import pyarrow.parquet as pq

ZONE_COUNT = 263
SLOT_COUNT = 48
WEEK_SLOT_COUNT = 7 * SLOT_COUNT
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATISTICS_PATH = PROJECT_ROOT / "data/processed/zone_time_statistics.parquet"
TRAVEL_TIME_PATH = PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"
TRAIN_PATH = PROJECT_ROOT / "data/processed/train_cleaned.parquet"

# Hyperparameters
GAMMA = 0.5  # discount factor for future utility
PICKUP_HALF_SATURATION = 240.0  # for multi-week training statistics
CANDIDATE_POOL_SIZE = 100  # number of candidates to consider


def recommend(
    current_datetime: datetime,
    current_location_id: int,
) -> list[int]:
    """Return the Top-3 LocationIDs for one simulator state."""
    if not isinstance(current_datetime, datetime):
        raise TypeError("current_datetime must be a datetime")
    if not 1 <= current_location_id <= ZONE_COUNT:
        raise ValueError("current_location_id must be in 1..263")

    current_zone = current_location_id
    origin_index = current_zone - 1

    # Compute baseline utility for all zones (single-step)
    target_time = _next_half_hour(current_datetime)
    slot = target_time.hour * 2 + target_time.minute // 30
    weekday = target_time.weekday()
    state = weekday * SLOT_COUNT + slot

    base_utility = _compute_baseline_utility(origin_index, state)
    arrival_slots = _compute_arrival_slots(origin_index, state)

    # Pre-select candidates: top N by baseline utility + current zone
    ordered_by_base = sorted(
        range(ZONE_COUNT),
        key=lambda z: (-base_utility[z], z),
    )
    candidates = set(ordered_by_base[:CANDIDATE_POOL_SIZE])
    candidates.add(origin_index)

    # Compute two-step utility for each candidate
    two_step_utility = list(base_utility)
    for z in candidates:
        # Arrival slot after moving to zone z
        arrival = arrival_slots[z]
        arr_weekday = arrival // SLOT_COUNT
        arr_slot = arrival % SLOT_COUNT

        # Pickup probability at arrival
        d = demand[arr_weekday][arr_slot][z]
        p_success = d / (d + PICKUP_HALF_SATURATION)

        # Expected fare
        f = mean_fare[arr_weekday][arr_slot][z]

        # Expected future utility after success: go to dropoff
        if transition_zone is not None:
            # Weighted by dropoff distribution
            future_success = 0.0
            for dropoff_z, trans_prob in enumerate(transition_zone[z]):
                if trans_prob > 0:
                    dur = mean_trip_duration_zone[z]
                    dur_slots = int(math.floor(dur / 30.0 + 0.5))
                    next_state = (arrival + 1 + dur_slots) % WEEK_SLOT_COUNT
                    next_weekday = next_state // SLOT_COUNT
                    next_slot = next_state % SLOT_COUNT
                    # Value of being at dropoff zone after trip
                    v_drop = _one_step_value(dropoff_z, next_weekday, next_slot)
                    future_success += trans_prob * v_drop
        else:
            future_success = 0.0

        # Expected future utility after failure: stay at z, advance 1 slot
        next_state_fail = (arrival + 1) % WEEK_SLOT_COUNT
        fail_weekday = next_state_fail // SLOT_COUNT
        fail_slot = next_state_fail % SLOT_COUNT
        future_fail = _one_step_value(z, fail_weekday, fail_slot)

        # Two-step utility
        u = p_success * (f + GAMMA * future_success) + (1 - p_success) * GAMMA * future_fail

        # Relocation cost adjustment
        if z == origin_index:
            move_cost = 0.0
        else:
            move_cost = travel_time[origin_index][z]
        if math.isfinite(move_cost) and move_cost >= 0:
            move_slots = int(math.floor(move_cost / 30.0 + 0.5))
            two_step_utility[z] = u / (move_slots + 1.0)
        else:
            two_step_utility[z] = 0.0

    # Top-3 selection
    ordered = sorted(
        range(1, ZONE_COUNT + 1),
        key=lambda z: (-two_step_utility[z - 1], z),
    )
    return ordered[:3]


def _one_step_value(zone_index: int, weekday: int, slot: int) -> float:
    """Compute the best single-step utility from a given state."""
    d = demand[weekday][slot][zone_index]
    f = mean_fare[weekday][slot][zone_index]
    p = d / (d + PICKUP_HALF_SATURATION) if d > 0 else 0.0
    return p * f


def _compute_baseline_utility(origin_index: int, state: int) -> list[float]:
    """Compute single-step utility for all zones (Baseline 2 style)."""
    weekday = state // SLOT_COUNT
    slot = state % SLOT_COUNT
    times = travel_time[origin_index]
    utility = [0.0] * ZONE_COUNT
    for j in range(ZONE_COUNT):
        if math.isfinite(times[j]) and times[j] >= 0:
            d = demand[weekday][slot][j]
            f = mean_fare[weekday][slot][j]
            utility[j] = d * f / (times[j] + 1.0)
    return utility


def _compute_arrival_slots(origin_index: int, state: int) -> list[int]:
    """Compute the arrival slot index for each destination."""
    times = travel_time[origin_index]
    arrival = [0] * ZONE_COUNT
    for j in range(ZONE_COUNT):
        if j == origin_index:
            arrival[j] = state
        elif math.isfinite(times[j]) and times[j] >= 0:
            move_slots = int(math.floor(times[j] / 30.0 + 0.5))
            arrival[j] = (state + move_slots) % WEEK_SLOT_COUNT
        else:
            arrival[j] = -1  # unreachable
    return arrival


def _load_zone_statistics() -> tuple:
    demand = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    mean_fare = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
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


def _load_transition_probabilities() -> list[list[float]]:
    """Load OD transition probabilities from cleaned training data."""
    trans = [[0.0] * ZONE_COUNT for _ in range(ZONE_COUNT)]
    pickup_counts = [0] * ZONE_COUNT

    table = pq.read_table(
        TRAIN_PATH,
        columns=["PULocationID", "DOLocationID"],
    ).to_pylist()

    for row in table:
        pu = int(row["PULocationID"]) - 1
        do = int(row["DOLocationID"]) - 1
        if 0 <= pu < ZONE_COUNT and 0 <= do < ZONE_COUNT:
            trans[pu][do] += 1.0
            pickup_counts[pu] += 1

    for pu in range(ZONE_COUNT):
        total = pickup_counts[pu]
        if total > 0:
            for do in range(ZONE_COUNT):
                trans[pu][do] /= total

    return trans


def _load_mean_trip_duration() -> list[float]:
    """Load mean trip duration per pickup zone."""
    means = [10.0] * ZONE_COUNT
    sums = [0.0] * ZONE_COUNT
    counts = [0] * ZONE_COUNT

    table = pq.read_table(
        TRAIN_PATH,
        columns=["PULocationID", "trip_duration"],
    ).to_pylist()

    for row in table:
        pu = int(row["PULocationID"]) - 1
        dur = float(row["trip_duration"])
        if 0 <= pu < ZONE_COUNT and dur > 0:
            sums[pu] += dur
            counts[pu] += 1

    for pu in range(ZONE_COUNT):
        if counts[pu] > 0:
            means[pu] = sums[pu] / counts[pu]
    return means


def _load_travel_time_matrix() -> list[list[float]]:
    with TRAVEL_TIME_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        matrix = []
        for row in reader:
            matrix.append([float(value) for value in row[1:]])
    return matrix


def _next_half_hour(value: datetime) -> datetime:
    slot_start = value.replace(
        minute=(value.minute // 30) * 30,
        second=0,
        microsecond=0,
    )
    return slot_start + timedelta(minutes=30)


# Global precomputation
demand, mean_fare = _load_zone_statistics()
travel_time = _load_travel_time_matrix()
transition_zone = _load_transition_probabilities()
mean_trip_duration_zone = _load_mean_trip_duration()

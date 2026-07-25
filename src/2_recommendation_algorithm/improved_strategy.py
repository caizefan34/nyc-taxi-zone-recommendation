"""Improved strategy: two-step finite horizon planning with transition probabilities."""
from __future__ import annotations

import math
from datetime import datetime

from src.common.config import get_config
from src.common.data_loader import DataLoader

ZONE_COUNT = get_config("domain.zone_count", 263)
SLOT_COUNT = get_config("domain.slot_count", 48)
WEEK_SLOT_COUNT = get_config("domain.week_slot_count", 336)

GAMMA = get_config("algorithm.gamma", 0.5)
PICKUP_HALF_SATURATION = get_config("algorithm.pickup_half_saturation", 240.0)
CANDIDATE_POOL_SIZE = get_config("algorithm.candidate_pool_size", 100)

loader = DataLoader()


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    """Return the Top-3 LocationIDs for one simulator state."""
    if not isinstance(current_datetime, datetime):
        raise TypeError("current_datetime must be a datetime")
    if not 1 <= current_location_id <= ZONE_COUNT:
        raise ValueError("current_location_id must be in 1..263")

    current_zone = current_location_id
    origin_index = current_zone - 1

    target_time = loader.next_half_hour(current_datetime)
    slot = target_time.hour * 2 + target_time.minute // 30
    weekday = target_time.weekday()
    state = weekday * SLOT_COUNT + slot

    base_utility = _compute_baseline_utility(origin_index, state)
    arrival_slots = _compute_arrival_slots(origin_index, state)

    ordered_by_base = sorted(range(ZONE_COUNT), key=lambda z: (-base_utility[z], z))
    candidates = set(ordered_by_base[:CANDIDATE_POOL_SIZE])
    candidates.add(origin_index)

    two_step_utility = list(base_utility)
    for z in candidates:
        arrival = arrival_slots[z]
        if arrival < 0:
            continue
        arr_weekday = arrival // SLOT_COUNT
        arr_slot = arrival % SLOT_COUNT

        d = demand[arr_weekday][arr_slot][z]
        p_success = d / (d + PICKUP_HALF_SATURATION)
        f = mean_fare[arr_weekday][arr_slot][z]

        if transition_zone is not None:
            future_success = 0.0
            for dropoff_z, trans_prob in enumerate(transition_zone[z]):
                if trans_prob > 0:
                    dur = mean_trip_duration_zone[z]
                    dur_slots = int(math.floor(dur / 30.0 + 0.5))
                    next_state = (arrival + 1 + dur_slots) % WEEK_SLOT_COUNT
                    next_wd = next_state // SLOT_COUNT
                    next_sl = next_state % SLOT_COUNT
                    v_drop = _one_step_value(dropoff_z, next_wd, next_sl)
                    future_success += trans_prob * v_drop
        else:
            future_success = 0.0

        next_state_fail = (arrival + 1) % WEEK_SLOT_COUNT
        fail_wd = next_state_fail // SLOT_COUNT
        fail_sl = next_state_fail % SLOT_COUNT
        future_fail = _one_step_value(z, fail_wd, fail_sl)

        u = p_success * (f + GAMMA * future_success) + (1 - p_success) * GAMMA * future_fail

        if z == origin_index:
            move_cost = 0.0
        else:
            move_cost = travel_time[origin_index][z]
        if math.isfinite(move_cost) and move_cost >= 0:
            move_slots = int(math.floor(move_cost / 30.0 + 0.5))
            two_step_utility[z] = u / (move_slots + 1.0)
        else:
            two_step_utility[z] = 0.0

    ordered = sorted(range(1, ZONE_COUNT + 1), key=lambda z: (-two_step_utility[z - 1], z))
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
            arrival[j] = -1
    return arrival


def _load_transition_probabilities():
    """Load OD transition probabilities from cleaned training data."""
    trans = [[0.0] * ZONE_COUNT for _ in range(ZONE_COUNT)]
    pickup_counts = [0] * ZONE_COUNT
    table = loader.load_train_data(columns=["PULocationID", "DOLocationID"])
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


def _load_mean_trip_duration():
    """Load mean trip duration per pickup zone."""
    means = [10.0] * ZONE_COUNT
    sums = [0.0] * ZONE_COUNT
    counts = [0] * ZONE_COUNT
    table = loader.load_train_data(columns=["PULocationID", "trip_duration"])
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


# Global precomputation at module load time
demand, mean_fare = loader.load_zone_statistics()
travel_time = loader.load_travel_time_matrix()
transition_zone = _load_transition_probabilities()
mean_trip_duration_zone = _load_mean_trip_duration()

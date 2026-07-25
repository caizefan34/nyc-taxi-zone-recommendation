"""Extension 2: Parameter sensitivity analysis of the two-step strategy."""
from __future__ import annotations
import csv
from datetime import datetime, timedelta
import importlib.util
import json
import math
from pathlib import Path
import sys as sys_module
from time import perf_counter_ns
from types import ModuleType

import numpy as np
import pyarrow.parquet as pq

from eval.offline_core import Query, ZONE_COUNT, SLOT_COUNT, validate_top3
from eval.validation_core import read_validation_answers
from eval.public_validation import read_public_queries, evaluate_validation


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUERIES_PATH = PROJECT_ROOT / "data/processed/validation_input.parquet"
ANSWERS_PATH = PROJECT_ROOT / "data/processed/validation_answers.parquet"
OUTPUT_PATH = PROJECT_ROOT / "outputs/extension_parameter_sensitivity.json"

# Parameter grid
GAMMA_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]
HALF_SAT_VALUES = [120, 240, 360]
POOL_SIZE_VALUES = [20, 50, 100]


def _create_strategy(gamma, half_sat, pool_size, output_path):
    """Create a strategy module with the given parameters."""
    code = f'''
import csv
import math
from datetime import datetime, timedelta
from pathlib import Path
import pyarrow.parquet as pq

ZONE_COUNT = 263
SLOT_COUNT = 48
WEEK_SLOT_COUNT = 7 * SLOT_COUNT
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATISTICS_PATH = PROJECT_ROOT / "data/processed/zone_time_statistics.parquet"
TRAVEL_TIME_PATH = PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"
TRAIN_PATH = PROJECT_ROOT / "data/processed/train_cleaned.parquet"

GAMMA = {gamma}
PICKUP_HALF_SATURATION = {half_sat}
CANDIDATE_POOL_SIZE = {pool_size}

def recommend(current_datetime, current_location_id):
    if not isinstance(current_datetime, datetime):
        raise TypeError("current_datetime must be a datetime")
    if not 1 <= current_location_id <= ZONE_COUNT:
        raise ValueError("current_location_id must be in 1..263")
    current_zone = current_location_id
    origin_index = current_zone - 1
    target_time = _next_half_hour(current_datetime)
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
        if arrival_slots[z] < 0:
            continue
        arrival = arrival_slots[z]
        arr_weekday = arrival // SLOT_COUNT
        arr_slot = arrival % SLOT_COUNT
        d = demand[arr_weekday][arr_slot][z]
        p_success = d / (d + PICKUP_HALF_SATURATION) if d > 0 else 0.0
        f = mean_fare[arr_weekday][arr_slot][z]
        future_success = 0.0
        for dropoff_z, trans_prob in enumerate(transition_zone[z]):
            if trans_prob > 0:
                dur = mean_trip_duration_zone[z]
                dur_slots = int(math.floor(dur / 30.0 + 0.5))
                next_state = (arrival + 1 + dur_slots) % WEEK_SLOT_COUNT
                next_weekday = next_state // SLOT_COUNT
                next_slot = next_state % SLOT_COUNT
                d2 = demand[next_weekday][next_slot][dropoff_z]
                v_drop = (d2 / (d2 + PICKUP_HALF_SATURATION) * mean_fare[next_weekday][next_slot][dropoff_z]) if d2 > 0 else 0.0
                future_success += trans_prob * v_drop
        next_state_fail = (arrival + 1) % WEEK_SLOT_COUNT
        fail_weekday = next_state_fail // SLOT_COUNT
        fail_slot = next_state_fail % SLOT_COUNT
        d3 = demand[fail_weekday][fail_slot][z]
        future_fail = (d3 / (d3 + PICKUP_HALF_SATURATION) * mean_fare[fail_weekday][fail_slot][z]) if d3 > 0 else 0.0
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

def _compute_baseline_utility(origin_index, state):
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

def _compute_arrival_slots(origin_index, state):
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

def _load_zone_statistics():
    demand = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    mean_fare = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    for row in pq.read_table(STATISTICS_PATH, columns=["pickup_location_id","weekday","time_slot","pickup_count","mean_fare_amount"]).to_pylist():
        loc = int(row["pickup_location_id"])
        wd = int(row["weekday"])
        ts = int(row["time_slot"])
        if 1 <= loc <= ZONE_COUNT:
            demand[wd][ts][loc - 1] = float(row["pickup_count"])
            rf = row["mean_fare_amount"]
            if rf is not None and math.isfinite(float(rf)):
                mean_fare[wd][ts][loc - 1] = max(0.0, float(rf))
    return demand, mean_fare

def _load_transition_probabilities():
    trans = [[0.0] * ZONE_COUNT for _ in range(ZONE_COUNT)]
    counts = [0] * ZONE_COUNT
    for row in pq.read_table(TRAIN_PATH, columns=["PULocationID","DOLocationID"]).to_pylist():
        pu = int(row["PULocationID"]) - 1
        do = int(row["DOLocationID"]) - 1
        if 0 <= pu < ZONE_COUNT and 0 <= do < ZONE_COUNT:
            trans[pu][do] += 1.0
            counts[pu] += 1
    for pu in range(ZONE_COUNT):
        if counts[pu] > 0:
            for do in range(ZONE_COUNT):
                trans[pu][do] /= counts[pu]
    return trans

def _load_mean_trip_duration():
    means = [10.0] * ZONE_COUNT
    sums = [0.0] * ZONE_COUNT
    counts = [0] * ZONE_COUNT
    for row in pq.read_table(TRAIN_PATH, columns=["PULocationID","trip_duration"]).to_pylist():
        pu = int(row["PULocationID"]) - 1
        dur = float(row["trip_duration"])
        if 0 <= pu < ZONE_COUNT and dur > 0:
            sums[pu] += dur
            counts[pu] += 1
    for pu in range(ZONE_COUNT):
        if counts[pu] > 0:
            means[pu] = sums[pu] / counts[pu]
    return means

def _load_travel_time_matrix():
    with TRAVEL_TIME_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        matrix = []
        for row in reader:
            matrix.append([float(v) for v in row[1:]])
    return matrix

def _next_half_hour(value):
    slot_start = value.replace(minute=(value.minute // 30) * 30, second=0, microsecond=0)
    return slot_start + timedelta(minutes=30)

demand, mean_fare = _load_zone_statistics()
travel_time = _load_travel_time_matrix()
transition_zone = _load_transition_probabilities()
mean_trip_duration_zone = _load_mean_trip_duration()
'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("param_strategy", output_path)
    module = importlib.util.module_from_spec(spec)
    sys_module.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parameters(gamma, half_sat, pool_size, queries, answers):
    tmp_path = PROJECT_ROOT / "src/3_extension_task/_param_strategy.py"
    module = _create_strategy(gamma, half_sat, pool_size, tmp_path)
    predictions = {}
    latencies_ns = []
    for query in queries:
        started = perf_counter_ns()
        pred = validate_top3(module.recommend(query.query_time, query.current_location_id))
        latencies_ns.append(perf_counter_ns() - started)
        predictions[query.query_id] = pred
    result = evaluate_validation(queries, answers, predictions, latencies_ns=latencies_ns, peak_tracemalloc_bytes=0)
    return {
        "gamma": gamma,
        "half_saturation": half_sat,
        "pool_size": pool_size,
        "ndcg_at_3": result["ndcg_at_3"],
        "hit_at_3": result["hit_at_3"],
        "utility_at_1": result["reference_two_step_utility_at_1"],
        "avg_time_ms": result["average_recommend_time_ms"],
    }


def main():
    queries = read_public_queries(QUERIES_PATH)
    answers = read_validation_answers(ANSWERS_PATH)
    results = []

    # Baseline
    r = test_parameters(0.5, 240, 50, queries, answers)
    results.append(r)
    print(f"Baseline: {r}")

    # Gamma sweep
    for g in GAMMA_VALUES:
        if g == 0.5:
            continue
        r = test_parameters(g, 240, 50, queries, answers)
        results.append(r)
        print(f"gamma={g}: {r}")

    # Half-saturation sweep
    for hs in HALF_SAT_VALUES:
        if hs == 240:
            continue
        r = test_parameters(0.5, hs, 50, queries, answers)
        results.append(r)
        print(f"half_sat={hs}: {r}")

    # Pool size sweep
    for ps in POOL_SIZE_VALUES:
        if ps == 50:
            continue
        r = test_parameters(0.5, 240, ps, queries, answers)
        results.append(r)
        print(f"pool_size={ps}: {r}")

    summary = {
        "description": "Parameter sensitivity analysis for two-step strategy",
        "default_parameters": {"gamma": 0.5, "half_saturation": 240, "pool_size": 50},
        "results": results,
        "best_by_ndcg": max(results, key=lambda r: r["ndcg_at_3"]),
        "best_by_utility": max(results, key=lambda r: r["utility_at_1"]),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

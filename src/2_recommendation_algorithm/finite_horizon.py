"""Generalized finite-horizon model-based planner for audit experiments."""
from __future__ import annotations

import math
from datetime import datetime

import numpy as np

from src.common.config import get_config
from src.common.data_loader import DataLoader

ZONE_COUNT = get_config("domain.zone_count", 263)
SLOT_COUNT = get_config("domain.slot_count", 48)
WEEK_SLOT_COUNT = get_config("domain.week_slot_count", 336)


class FiniteHorizonPlanner:
    """Precompute truncated Bellman evaluation for horizons 1..max_horizon.

    The continuation policy waits for a pickup in the reached zone.  It does
    not optimize a fresh relocation action at future states, matching the
    continuation assumption used by the repository's two-step strategy.
    """

    def __init__(
        self,
        *,
        max_horizon: int = 5,
        gamma: float = 0.5,
        pickup_half_saturation: float = 240.0,
        candidate_pool_size: int = 100,
    ) -> None:
        if max_horizon < 1:
            raise ValueError("max_horizon must be positive")
        if not 0.0 <= gamma < 1.0:
            raise ValueError("gamma must be in [0, 1)")
        self.max_horizon = max_horizon
        self.gamma = gamma
        self.pickup_half_saturation = pickup_half_saturation
        self.candidate_pool_size = candidate_pool_size
        self.loader = DataLoader()
        demand, fare = self.loader.load_zone_statistics()
        self.demand = np.asarray(demand, dtype=float).reshape(WEEK_SLOT_COUNT, ZONE_COUNT)
        self.fare = np.asarray(fare, dtype=float).reshape(WEEK_SLOT_COUNT, ZONE_COUNT)
        self.travel_time = np.asarray(self.loader.load_travel_time_matrix(), dtype=float)
        self.transition, self.duration_slots = self._load_transition_model()
        self.values = self._precompute_values()

    def _load_transition_model(self) -> tuple[np.ndarray, np.ndarray]:
        rows = self.loader.load_train_data(columns=["PULocationID", "DOLocationID", "trip_duration"])
        transition = np.zeros((ZONE_COUNT, ZONE_COUNT), dtype=float)
        duration_sum = np.zeros(ZONE_COUNT, dtype=float)
        count = np.zeros(ZONE_COUNT, dtype=float)
        for row in rows:
            pickup = int(row["PULocationID"]) - 1
            dropoff = int(row["DOLocationID"]) - 1
            duration = float(row["trip_duration"])
            if 0 <= pickup < ZONE_COUNT and 0 <= dropoff < ZONE_COUNT and duration > 0.0:
                transition[pickup, dropoff] += 1.0
                duration_sum[pickup] += duration
                count[pickup] += 1.0
        transition = np.divide(
            transition,
            count[:, None],
            out=np.zeros_like(transition),
            where=count[:, None] > 0.0,
        )
        mean_duration = np.divide(duration_sum, count, out=np.full(ZONE_COUNT, 10.0), where=count > 0.0)
        duration_slots = np.floor(mean_duration / 30.0 + 0.5).astype(int)
        return transition, duration_slots

    def _precompute_values(self) -> dict[int, np.ndarray]:
        probability = np.divide(
            self.demand,
            self.demand + self.pickup_half_saturation,
            out=np.zeros_like(self.demand),
            where=self.demand > 0.0,
        )
        values = {1: probability * self.fare}
        zones = np.arange(ZONE_COUNT)
        for horizon in range(2, self.max_horizon + 1):
            previous = values[horizon - 1]
            current = np.zeros_like(previous)
            for state in range(WEEK_SLOT_COUNT):
                next_success_states = (state + 1 + self.duration_slots) % WEEK_SLOT_COUNT
                success = np.sum(self.transition * previous[next_success_states, :], axis=1)
                failure = previous[(state + 1) % WEEK_SLOT_COUNT, zones]
                p = probability[state]
                current[state] = p * (self.fare[state] + self.gamma * success) + (1.0 - p) * self.gamma * failure
            values[horizon] = current
        return values

    def recommend(self, current_datetime: datetime, current_location_id: int, *, horizon: int = 2) -> list[int]:
        if horizon not in self.values:
            raise ValueError(f"horizon must be in 1..{self.max_horizon}")
        if not isinstance(current_datetime, datetime):
            raise TypeError("current_datetime must be a datetime")
        if not 1 <= current_location_id <= ZONE_COUNT:
            raise ValueError("current_location_id must be in 1..263")
        return self._rank(current_datetime, current_location_id, horizon)

    def recommend_adaptive(self, current_datetime: datetime, current_location_id: int) -> list[int]:
        previous = self._rank(current_datetime, current_location_id, 1)
        for horizon in range(2, self.max_horizon + 1):
            current = self._rank(current_datetime, current_location_id, horizon)
            if current == previous:
                return current
            previous = current
        return previous

    def _rank(self, current_datetime: datetime, current_location_id: int, horizon: int) -> list[int]:
        target = self.loader.next_half_hour(current_datetime)
        state = target.weekday() * SLOT_COUNT + target.hour * 2 + target.minute // 30
        origin = current_location_id - 1
        times = self.travel_time[origin]
        reachable = np.isfinite(times) & (times >= 0.0)
        move_slots = np.zeros(ZONE_COUNT, dtype=int)
        movable = reachable & (np.arange(ZONE_COUNT) != origin)
        move_slots[movable] = np.floor(times[movable] / 30.0 + 0.5).astype(int)
        base = np.zeros(ZONE_COUNT, dtype=float)
        base[reachable] = self.demand[state, reachable] * self.fare[state, reachable] / (times[reachable] + 1.0)
        candidates = np.argsort(-base, kind="stable")[: self.candidate_pool_size]
        if origin not in candidates:
            candidates = np.append(candidates, origin)
        scores = np.full(ZONE_COUNT, -math.inf, dtype=float)
        arrivals = (state + move_slots) % WEEK_SLOT_COUNT
        scores[candidates] = self.values[horizon][arrivals[candidates], candidates] / (move_slots[candidates] + 1.0)
        ordered = np.lexsort((np.arange(ZONE_COUNT), -scores))[:3]
        return (ordered + 1).tolist()


_DEFAULT_PLANNER: FiniteHorizonPlanner | None = None


def get_planner() -> FiniteHorizonPlanner:
    global _DEFAULT_PLANNER
    if _DEFAULT_PLANNER is None:
        _DEFAULT_PLANNER = FiniteHorizonPlanner(max_horizon=5)
    return _DEFAULT_PLANNER


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    """Default compatibility interface uses horizon two."""
    return get_planner().recommend(current_datetime, current_location_id, horizon=2)

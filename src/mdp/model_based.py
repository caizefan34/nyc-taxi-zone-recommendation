"""Synchronous value iteration for the repository's estimated taxi model."""
from __future__ import annotations

import math
from datetime import datetime

import numpy as np

from src.common.config import get_config
from src.common.data_loader import DataLoader
from src.common.logging_utils import get_logger

logger = get_logger(__name__)


def bellman_backup(
    previous: np.ndarray,
    probability: np.ndarray,
    fare: np.ndarray,
    transition: np.ndarray,
    duration_slots: np.ndarray,
    move_slots: np.ndarray,
    reachable: np.ndarray,
    gamma: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply one Bellman optimality backup to a finite periodic model.

    Returns the new value table and greedy action table, both indexed by
    `[time_state, origin_zone]`.
    """
    state_count, zone_count = previous.shape
    if probability.shape != previous.shape or fare.shape != previous.shape:
        raise ValueError("probability, fare, and value tables must have the same shape")
    if transition.shape != (zone_count, zone_count):
        raise ValueError("transition must have shape (zones, zones)")
    if move_slots.shape != (zone_count, zone_count) or reachable.shape != move_slots.shape:
        raise ValueError("movement arrays must have shape (zones, zones)")

    states = np.arange(state_count)
    zones = np.arange(zone_count)
    success = np.zeros_like(previous)
    for action in zones:
        next_states = (states + 1 + int(duration_slots[action])) % state_count
        success[:, action] = previous[next_states] @ transition[action]
    failure = previous[(states + 1) % state_count]

    values = np.zeros_like(previous)
    policy = np.zeros((state_count, zone_count), dtype=np.int32)
    destinations = np.broadcast_to(zones, move_slots.shape)
    for state in states:
        arrivals = (state + move_slots) % state_count
        p = probability[arrivals, destinations]
        rewards = fare[arrivals, destinations]
        continuation_success = success[arrivals, destinations]
        continuation_failure = failure[arrivals, destinations]
        q_values = p * (rewards + gamma * continuation_success) + (1.0 - p) * gamma * continuation_failure
        q_values = np.where(reachable, q_values, -np.inf)
        policy[state] = np.argmax(q_values, axis=1)
        values[state] = np.max(q_values, axis=1)
    return values, policy


class MDPValueIteration:
    """Value iteration over relocation, pickup success/failure, and OD transitions."""

    def __init__(
        self,
        gamma: float = 0.5,
        epsilon: float = 1e-4,
        max_iterations: int = 100,
    ) -> None:
        if not 0.0 <= gamma < 1.0:
            raise ValueError("gamma must be in [0, 1)")
        self.gamma = gamma
        self.epsilon = epsilon
        self.max_iterations = max_iterations
        self.loader = DataLoader()
        self.zone_count = get_config("domain.zone_count", 263)
        self.slot_count = get_config("domain.slot_count", 48)
        self.state_count = get_config("domain.week_slot_count", 336)
        demand, fare = self.loader.load_zone_statistics()
        demand_array = np.asarray(demand, dtype=float).reshape(self.state_count, self.zone_count)
        self.fare = np.asarray(fare, dtype=float).reshape(self.state_count, self.zone_count)
        half_saturation = get_config("algorithm.pickup_half_saturation", 240.0)
        self.probability = np.divide(
            demand_array,
            demand_array + half_saturation,
            out=np.zeros_like(demand_array),
            where=demand_array > 0.0,
        )
        self.transition, self.duration_slots = self._load_transition_model()
        self.move_slots, self.reachable = self._load_movement_model()
        self.values, self.policy, self.iterations, self.converged = self._solve()

    def _load_transition_model(self) -> tuple[np.ndarray, np.ndarray]:
        transition = np.zeros((self.zone_count, self.zone_count), dtype=float)
        duration_sum = np.zeros(self.zone_count, dtype=float)
        count = np.zeros(self.zone_count, dtype=float)
        for row in self.loader.load_train_data(columns=["PULocationID", "DOLocationID", "trip_duration"]):
            pickup = int(row["PULocationID"]) - 1
            dropoff = int(row["DOLocationID"]) - 1
            duration = float(row["trip_duration"])
            if 0 <= pickup < self.zone_count and 0 <= dropoff < self.zone_count and duration > 0.0:
                transition[pickup, dropoff] += 1.0
                duration_sum[pickup] += duration
                count[pickup] += 1.0
        transition = np.divide(
            transition,
            count[:, None],
            out=np.zeros_like(transition),
            where=count[:, None] > 0.0,
        )
        missing = np.flatnonzero(transition.sum(axis=1) == 0.0)
        transition[missing, missing] = 1.0
        duration = np.divide(duration_sum, count, out=np.full(self.zone_count, 10.0), where=count > 0.0)
        return transition, np.floor(duration / 30.0 + 0.5).astype(np.int32)

    def _load_movement_model(self) -> tuple[np.ndarray, np.ndarray]:
        travel = np.asarray(self.loader.load_travel_time_matrix(), dtype=float)
        reachable = np.isfinite(travel) & (travel >= 0.0)
        move_slots = np.zeros_like(travel, dtype=np.int32)
        move_slots[reachable] = np.floor(travel[reachable] / 30.0 + 0.5).astype(np.int32)
        np.fill_diagonal(move_slots, 0)
        np.fill_diagonal(reachable, True)
        return move_slots, reachable

    def _solve(self) -> tuple[np.ndarray, np.ndarray, int, bool]:
        values = np.zeros((self.state_count, self.zone_count), dtype=float)
        policy = np.zeros((self.state_count, self.zone_count), dtype=np.int32)
        for iteration in range(1, self.max_iterations + 1):
            updated, policy = bellman_backup(
                values,
                self.probability,
                self.fare,
                self.transition,
                self.duration_slots,
                self.move_slots,
                self.reachable,
                self.gamma,
            )
            delta = float(np.max(np.abs(updated - values)))
            values = updated
            if iteration == 1 or iteration % 10 == 0:
                logger.info("MDP iteration=%d delta=%.6f", iteration, delta)
            if delta < self.epsilon:
                return values, policy, iteration, True
        return values, policy, self.max_iterations, False

    def q_values(self, state: int, origin_index: int) -> np.ndarray:
        """Return converged action values for one state and origin."""
        if not 0 <= state < self.state_count or not 0 <= origin_index < self.zone_count:
            raise ValueError("state or origin is out of range")
        states = np.arange(self.state_count)
        success = np.zeros((self.state_count, self.zone_count), dtype=float)
        for action in range(self.zone_count):
            next_states = (states + 1 + int(self.duration_slots[action])) % self.state_count
            success[:, action] = self.values[next_states] @ self.transition[action]
        failure = self.values[(states + 1) % self.state_count]
        arrivals = (state + self.move_slots[origin_index]) % self.state_count
        zones = np.arange(self.zone_count)
        p = self.probability[arrivals, zones]
        q = p * (self.fare[arrivals, zones] + self.gamma * success[arrivals, zones])
        q += (1.0 - p) * self.gamma * failure[arrivals, zones]
        return np.where(self.reachable[origin_index], q, -math.inf)

    def recommend(self, current_datetime: datetime, current_location_id: int) -> list[int]:
        if not isinstance(current_datetime, datetime):
            raise TypeError("current_datetime must be a datetime")
        if not 1 <= current_location_id <= self.zone_count:
            raise ValueError("current_location_id is out of range")
        state = self.loader.datetime_to_state(current_datetime)
        q = self.q_values(state, current_location_id - 1)
        ordered = np.lexsort((np.arange(self.zone_count), -q))[:3]
        return (ordered + 1).tolist()


_SOLVER: MDPValueIteration | None = None


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    global _SOLVER
    if _SOLVER is None:
        _SOLVER = MDPValueIteration()
    return _SOLVER.recommend(current_datetime, current_location_id)


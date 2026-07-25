"""MDP Value Iteration solver for taxi zone recommendation.

Implements Bellman Equation, Value Iteration, and Policy Extraction
for the full 263 x 336 state space.

This module provides an offline precomputation approach:
- Precomputes value function for all states
- Online query is a simple O(263) lookup
- Compatible with the existing recommend() interface
"""
from __future__ import annotations
import math
from datetime import datetime

from src.common.data_loader import DataLoader
from src.common.config import get_config
from src.common.logging_utils import get_logger

logger = get_logger(__name__)

ZONE_COUNT = get_config("domain.zone_count", 263)
SLOT_COUNT = get_config("domain.slot_count", 48)
WEEK_SLOT_COUNT = get_config("domain.week_slot_count", 336)
GAMMA = get_config("algorithm.gamma", 0.5)
PICKUP_HALF_SATURATION = get_config("algorithm.pickup_half_saturation", 240.0)
TOP_K = get_config("algorithm.top_k", 3)

loader = DataLoader()


class MDPValueIteration:
    """MDP solver using Value Iteration.

    Attributes:
        values: Precomputed value function [weekday][slot][zone_index]
        demand: Pickup demand statistics
        mean_fare: Mean fare statistics
        travel_time: Travel time matrix
        converged: Whether value iteration converged
    """

    def __init__(self, gamma: float = GAMMA, epsilon: float = 1e-4, max_iterations: int = 200):
        """Initialize and run value iteration.

        Args:
            gamma: Discount factor.
            epsilon: Convergence threshold.
            max_iterations: Maximum value iteration steps.
        """
        self.gamma = gamma
        self.epsilon = epsilon
        self.max_iterations = max_iterations
        self.converged = False

        logger.info("Loading data...")
        self.demand, self.mean_fare = loader.load_zone_statistics()
        self.travel_time = loader.load_travel_time_matrix()

        logger.info("Running value iteration (S=%d, A=%d)...", WEEK_SLOT_COUNT * ZONE_COUNT, ZONE_COUNT)
        self.values = self._value_iteration()
        logger.info("Value iteration complete. Converged: %s", self.converged)

    def _compute_reward(self, origin_idx: int, dest_idx: int, weekday: int, slot: int) -> float:
        """Compute the expected immediate reward for moving from origin to destination."""
        d = self.demand[weekday][slot][dest_idx]
        f = self.mean_fare[weekday][slot][dest_idx]
        if d <= 0:
            return 0.0
        p_success = d / (d + PICKUP_HALF_SATURATION)
        return p_success * f

    def _compute_arrival_state(self, origin_idx: int, dest_idx: int, state: int) -> int:
        """Compute arrival state (weekday_slot index) after traveling from origin to dest."""
        if dest_idx == origin_idx:
            return state
        tt = self.travel_time[origin_idx][dest_idx]
        if math.isinf(tt) or tt < 0:
            return -1
        move_slots = int(math.floor(tt / 30.0 + 0.5))
        return (state + move_slots) % WEEK_SLOT_COUNT

    def _value_iteration(self) -> list[list[list[float]]]:
        """Run value iteration until convergence."""
        V = [[[0.0] * ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]

        for iteration in range(self.max_iterations):
            delta = 0.0
            for weekday in range(7):
                for slot in range(SLOT_COUNT):
                    state = weekday * SLOT_COUNT + slot
                    for origin_idx in range(ZONE_COUNT):
                        best_value = 0.0
                        for dest_idx in range(ZONE_COUNT):
                            arr_state = self._compute_arrival_state(origin_idx, dest_idx, state)
                            if arr_state < 0:
                                continue
                            reward = self._compute_reward(origin_idx, dest_idx, arr_state // SLOT_COUNT, arr_state % SLOT_COUNT)
                            arr_wd = arr_state // SLOT_COUNT
                            arr_sl = arr_state % SLOT_COUNT
                            future = self.gamma * V[arr_wd][arr_sl][dest_idx]
                            value = reward + future
                            if value > best_value:
                                best_value = value
                        old_val = V[weekday][slot][origin_idx]
                        V[weekday][slot][origin_idx] = best_value
                        delta = max(delta, abs(best_value - old_val))
            if iteration % 20 == 0:
                logger.info("Iteration %d, delta=%.6f", iteration, delta)
            if delta < self.epsilon:
                self.converged = True
                break
        return V

    def extract_policy(self, state: int) -> list[int]:
        """Extract optimal action (top-K zones) for a given state.

        Args:
            state: Combined weekday_slot index [0, 336).
        Returns:
            List of top-K zone IDs (1-based).
        """
        weekday = state // SLOT_COUNT
        slot = state % SLOT_COUNT
        utilities = []
        for dest_idx in range(ZONE_COUNT):
            arr_state = self._compute_arrival_state(dest_idx, dest_idx, state)
            if arr_state >= 0:
                reward = self._compute_reward(dest_idx, dest_idx, arr_state // SLOT_COUNT, arr_state % SLOT_COUNT)
                arr_wd = arr_state // SLOT_COUNT
                arr_sl = arr_state % SLOT_COUNT
                future = self.gamma * self.values[arr_wd][arr_sl][dest_idx]
                utilities.append((dest_idx + 1, reward + future))
            else:
                utilities.append((dest_idx + 1, 0.0))
        utilities.sort(key=lambda x: (-x[1], x[0]))
        return [z for z, _ in utilities[:TOP_K]]

    def recommend(self, current_datetime: datetime, current_location_id: int) -> list[int]:
        """Recommend top-K zones for a given state.

        Args:
            current_datetime: Current time.
            current_location_id: Current zone ID (1-based).
        Returns:
            List of top-K recommended zone IDs.
        """
        state = loader.datetime_to_state(current_datetime)
        return self.extract_policy(state)


# Module-level singleton for compatibility
_solver = None


def get_solver():
    """Get or create the MDP solver singleton."""
    global _solver
    if _solver is None:
        _solver = MDPValueIteration()
    return _solver


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    """Compatibility wrapper: recommend using MDP value iteration.

    Args:
        current_datetime: Current time.
        current_location_id: Current zone ID (1-based).
    Returns:
        List of top-3 recommended zone IDs.
    """
    return get_solver().recommend(current_datetime, current_location_id)

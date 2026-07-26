"""Gymnasium environment backed by finite trip inventory and background supply."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping, Sequence

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.eval.rollout_core import MarketCell, minutes_to_slots
from src.simulator.multi_agent import TripRecord, market_key, scale_trip_inventory

SLOT_MINUTES = 30
WEEK_SLOTS = 336


@dataclass(frozen=True)
class RLEnvConfig:
    """Controlled driver and mean-field background fleet configuration."""

    candidate_count: int = 20
    background_driver_count: int = 49
    demand_supply_ratio: float = 1.0
    start_location_id: int | None = None
    reward_scale: float = 0.05
    relocation_penalty: float = 0.25
    failed_pickup_penalty: float = 1.0

    def __post_init__(self) -> None:
        if self.candidate_count <= 0:
            raise ValueError("candidate_count must be positive")
        if self.background_driver_count < 0:
            raise ValueError("background_driver_count cannot be negative")
        if not math.isfinite(self.demand_supply_ratio) or self.demand_supply_ratio < 0.0:
            raise ValueError("demand_supply_ratio must be finite and non-negative")
        if not math.isfinite(self.reward_scale) or self.reward_scale <= 0.0:
            raise ValueError("reward_scale must be finite and positive")


class ObservationEncoder:
    """Encode a decision state and its heuristic candidate set without target leakage."""

    def __init__(
        self,
        demand: np.ndarray,
        fare: np.ndarray,
        travel_times: Sequence[Sequence[float]] | np.ndarray,
        *,
        candidate_count: int,
        background_driver_count: int,
    ) -> None:
        self.demand = np.asarray(demand, dtype=np.float32)
        self.fare = np.asarray(fare, dtype=np.float32)
        self.travel_times = np.asarray(travel_times, dtype=np.float32)
        if self.demand.shape != self.fare.shape or self.demand.ndim != 2:
            raise ValueError("demand and fare must have matching two-dimensional shapes")
        if self.demand.shape[0] != WEEK_SLOTS:
            raise ValueError("demand and fare must contain 336 weekly slots")
        self.zone_count = self.demand.shape[1]
        if self.travel_times.shape != (self.zone_count, self.zone_count):
            raise ValueError("travel_times must match the feature zone count")
        if not 1 <= candidate_count <= self.zone_count:
            raise ValueError("candidate_count must be in 1..zone_count")
        self.candidate_count = candidate_count
        self.background_driver_count = background_driver_count
        self.demand_scale = max(float(self.demand.max()), 1.0)
        self.fare_scale = max(float(self.fare.max()), 1.0)
        finite_times = self.travel_times[np.isfinite(self.travel_times)]
        self.travel_scale = max(float(finite_times.max()), 1.0)
        self.utility_scale = self.demand_scale * self.fare_scale
        self.observation_size = 5 + 6 * candidate_count

    @staticmethod
    def state_index(value: datetime) -> int:
        return value.weekday() * 48 + value.hour * 2 + value.minute // SLOT_MINUTES

    def encode(self, value: datetime, current_location_id: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not 1 <= current_location_id <= self.zone_count:
            raise ValueError(f"current_location_id must be in 1..{self.zone_count}")
        state = self.state_index(value)
        origin = current_location_id - 1
        times = self.travel_times[origin]
        reachable = np.isfinite(times) & (times >= 0.0)
        utility = np.full(self.zone_count, -np.inf, dtype=np.float32)
        utility[reachable] = self.demand[state, reachable] * self.fare[state, reachable] / (
            times[reachable] + 1.0
        )
        ordered = np.lexsort((np.arange(self.zone_count), -utility))
        valid = ordered[np.isfinite(utility[ordered])][: self.candidate_count]
        candidates = np.full(self.candidate_count, -1, dtype=np.int32)
        candidates[: len(valid)] = valid
        action_mask = candidates >= 0

        slot = value.hour * 2 + value.minute // SLOT_MINUTES
        week_slot = state
        observation = np.zeros(self.observation_size, dtype=np.float32)
        observation[:5] = [
            math.sin(2.0 * math.pi * slot / 48.0),
            math.cos(2.0 * math.pi * slot / 48.0),
            math.sin(2.0 * math.pi * week_slot / WEEK_SLOTS),
            math.cos(2.0 * math.pi * week_slot / WEEK_SLOTS),
            origin / max(self.zone_count - 1, 1),
        ]
        total_demand = max(float(self.demand[state].sum()), 1.0)
        for index, zone in enumerate(candidates):
            if zone < 0:
                continue
            offset = 5 + index * 6
            expected_supply = self.background_driver_count * float(self.demand[state, zone]) / total_demand
            observation[offset : offset + 6] = [
                self.demand[state, zone] / self.demand_scale,
                self.fare[state, zone] / self.fare_scale,
                times[zone] / self.travel_scale,
                expected_supply / max(self.background_driver_count, 1),
                utility[zone] / self.utility_scale,
                zone / max(self.zone_count - 1, 1),
            ]
        return observation, candidates, action_mask


class TaxiRepositionEnv(gym.Env[np.ndarray, int]):
    """Control one driver while seeded background supply depletes the same market."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        market: Mapping[int, MarketCell],
        demand_features: np.ndarray,
        fare_features: np.ndarray,
        travel_times: Sequence[Sequence[float]] | np.ndarray,
        start: datetime,
        end: datetime,
        config: RLEnvConfig | None = None,
    ) -> None:
        super().__init__()
        self.config = config or RLEnvConfig()
        self.market = market
        self.start = start
        self.end = end
        horizon_seconds = (end - start).total_seconds()
        if horizon_seconds <= 0.0 or horizon_seconds % (SLOT_MINUTES * 60) != 0.0:
            raise ValueError("environment horizon must use positive whole half-hour slots")
        self.horizon_slots = int(horizon_seconds // (SLOT_MINUTES * 60))
        self.encoder = ObservationEncoder(
            demand_features,
            fare_features,
            travel_times,
            candidate_count=self.config.candidate_count,
            background_driver_count=self.config.background_driver_count,
        )
        self.travel_times = self.encoder.travel_times
        self.zone_count = self.encoder.zone_count
        if self.config.start_location_id is not None and not 1 <= self.config.start_location_id <= self.zone_count:
            raise ValueError(f"start_location_id must be in 1..{self.zone_count}")
        self.action_space = spaces.Discrete(self.config.candidate_count)
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.encoder.observation_size,),
            dtype=np.float32,
        )
        self.inventory: dict[int, list[TripRecord]] = {}
        self.current_time = start
        self.current_location_id = 1
        self.candidates = np.zeros(self.config.candidate_count, dtype=np.int32)
        self.action_mask = np.zeros(self.config.candidate_count, dtype=bool)
        self.initial_trip_inventory = 0
        self.total_fare = 0.0
        self.fulfilled_trips = 0

    def _observation(self) -> tuple[np.ndarray, dict[str, object]]:
        value = min(self.current_time, self.end - timedelta(minutes=SLOT_MINUTES))
        observation, candidates, action_mask = self.encoder.encode(value, self.current_location_id)
        self.candidates = candidates
        self.action_mask = action_mask
        info = {
            "action_mask": action_mask.copy(),
            "candidate_zones": np.where(action_mask, candidates + 1, 0),
            "current_time": self.current_time,
            "current_location_id": self.current_location_id,
            "remaining_trip_inventory": sum(len(trips) for trips in self.inventory.values()),
            "total_fare": self.total_fare,
            "fulfilled_trips": self.fulfilled_trips,
        }
        return observation, info

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, dict[str, object]]:
        super().reset(seed=seed)
        del options
        total_drivers = self.config.background_driver_count + 1
        target_count = math.floor(
            self.config.demand_supply_ratio * total_drivers * self.horizon_slots + 0.5
        )
        inventory_seed = int(self.np_random.integers(0, 2**32 - 1))
        self.inventory = scale_trip_inventory(
            self.market,
            target_count=target_count,
            rng=random.Random(inventory_seed),
        )
        self.initial_trip_inventory = sum(len(trips) for trips in self.inventory.values())
        self.current_time = self.start
        if self.config.start_location_id is None:
            state = self.encoder.state_index(self.start)
            weights = self.encoder.demand[state].astype(float)
            probabilities = weights / weights.sum() if weights.sum() > 0.0 else None
            self.current_location_id = int(self.np_random.choice(self.zone_count, p=probabilities)) + 1
        else:
            self.current_location_id = self.config.start_location_id
        self.total_fare = 0.0
        self.fulfilled_trips = 0
        return self._observation()

    def _background_allocation(self, value: datetime) -> np.ndarray:
        state = self.encoder.state_index(value)
        weights = self.encoder.demand[state].astype(float)
        if weights.sum() <= 0.0 or self.config.background_driver_count == 0:
            return np.zeros(self.zone_count, dtype=int)
        return self.np_random.multinomial(
            self.config.background_driver_count,
            weights / weights.sum(),
        )

    def _consume_slot(self, value: datetime, *, focal_zone: int | None = None) -> TripRecord | None:
        background = self._background_allocation(value)
        focal_trip = None
        for zone_index, background_count in enumerate(background):
            key = market_key(value, zone_index + 1, self.start, self.zone_count)
            trips = self.inventory.get(key, [])
            if focal_zone == zone_index + 1:
                contender_count = int(background_count) + 1
                match_count = min(contender_count, len(trips))
                focal_success = match_count > 0 and self.np_random.random() < match_count / contender_count
                if focal_success:
                    focal_trip = trips.pop()
                    match_count -= 1
                for _ in range(match_count):
                    trips.pop()
            else:
                for _ in range(min(int(background_count), len(trips))):
                    trips.pop()
        return focal_trip

    def _consume_background_until(self, stop: datetime) -> None:
        value = self.current_time
        while value < stop and value < self.end:
            self._consume_slot(value)
            value += timedelta(minutes=SLOT_MINUTES)

    def step(self, action: int):
        if not self.action_space.contains(action):
            raise ValueError(f"action must be in 0..{self.config.candidate_count - 1}")
        if self.current_time >= self.end:
            raise RuntimeError("step called after episode termination")
        valid_action = bool(self.action_mask[action])
        target_zone = int(self.candidates[action]) + 1 if valid_action else self.current_location_id
        travel_minutes = (
            float(self.travel_times[self.current_location_id - 1, target_zone - 1])
            if valid_action
            else 0.0
        )
        relocation_slots = minutes_to_slots(travel_minutes)
        arrival_time = self.current_time + timedelta(minutes=relocation_slots * SLOT_MINUTES)
        self._consume_background_until(arrival_time)
        self.current_time = arrival_time
        self.current_location_id = target_zone

        trip = None if self.current_time >= self.end else self._consume_slot(self.current_time, focal_zone=target_zone)
        reward_dollars = -self.config.relocation_penalty * relocation_slots
        pickup_success = trip is not None
        if trip is None:
            reward_dollars -= self.config.failed_pickup_penalty
            next_time = self.current_time + timedelta(minutes=SLOT_MINUTES)
        else:
            reward_dollars += trip.fare
            self.total_fare += trip.fare
            self.fulfilled_trips += 1
            self.current_location_id = trip.dropoff_zone
            next_time = self.current_time + timedelta(
                minutes=(1 + trip.duration_slots) * SLOT_MINUTES
            )
        self.current_time += timedelta(minutes=SLOT_MINUTES)
        self._consume_background_until(next_time)
        self.current_time = next_time
        terminated = self.current_time >= self.end
        observation, info = self._observation()
        info.update(
            {
                "pickup_success": pickup_success,
                "trip_fare": 0.0 if trip is None else trip.fare,
                "relocation_slots": relocation_slots,
                "invalid_action": not valid_action,
            }
        )
        return observation, float(reward_dollars * self.config.reward_scale), terminated, False, info

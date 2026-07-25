"""Event-driven taxi simulator with finite demand and competing drivers."""
from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping, Sequence

import numpy as np

from src.eval.offline_core import validate_top3
from src.eval.rollout_core import MarketCell, Strategy, choose_destination, minutes_to_slots

SLOT_MINUTES = 30


@dataclass(frozen=True)
class MultiAgentConfig:
    """Configuration shared by all drivers in one rollout."""

    driver_count: int
    demand_supply_ratio: float = 1.0
    seed: int = 20230722
    start_location_ids: tuple[int, ...] = (132,)

    def __post_init__(self) -> None:
        if self.driver_count <= 0:
            raise ValueError("driver_count must be positive")
        if not math.isfinite(self.demand_supply_ratio) or self.demand_supply_ratio < 0.0:
            raise ValueError("demand_supply_ratio must be finite and non-negative")
        if len(self.start_location_ids) not in (1, self.driver_count):
            raise ValueError("start_location_ids must contain one shared zone or one zone per driver")


@dataclass(frozen=True)
class MultiAgentResult:
    """Aggregate market and driver outcomes from one deterministic seed."""

    driver_count: int
    configured_demand_supply_ratio: float
    realized_demand_supply_ratio: float
    initial_trip_inventory: int
    remaining_trip_inventory: int
    fulfilled_trips: int
    demand_fulfillment_rate: float
    total_revenue: float
    average_driver_revenue: float
    average_idle_minutes: float
    driver_utilization: float
    pickup_attempts: int
    failed_pickup_attempts: int
    competing_pickup_attempts: int
    saturated_pickup_attempts: int
    saturated_zone_slots: int
    zone_saturation_rate: float
    peak_zone_supply: int
    relocation_count: int
    average_relocation_minutes: float


@dataclass(frozen=True)
class _Trip:
    dropoff_zone: int
    fare: float
    duration_slots: int


@dataclass
class _Driver:
    location_id: int
    revenue: float = 0.0
    trip_minutes: float = 0.0
    relocation_minutes: float = 0.0
    served_trips: int = 0
    failed_attempts: int = 0


def _scaled_inventory(
    market: Mapping[int, MarketCell],
    *,
    target_count: int,
    rng: random.Random,
) -> dict[int, list[_Trip]]:
    source = {
        key: [
            _Trip(int(cell.dropoff_zones[index]), float(cell.fares[index]), int(cell.duration_slots[index]))
            for index in range(len(cell))
        ]
        for key, cell in market.items()
        if len(cell) > 0
    }
    source_count = sum(len(trips) for trips in source.values())
    if target_count == 0:
        return {}
    if source_count == 0:
        raise ValueError("positive demand_supply_ratio requires at least one market trip")

    scale = target_count / source_count
    desired = {key: len(trips) * scale for key, trips in source.items()}
    counts = {key: math.floor(value) for key, value in desired.items()}
    residual = target_count - sum(counts.values())
    ranked = sorted(
        source,
        key=lambda key: (desired[key] - counts[key], rng.random()),
        reverse=True,
    )
    for key in ranked[:residual]:
        counts[key] += 1

    inventory: dict[int, list[_Trip]] = {}
    for key, trips in source.items():
        count = counts[key]
        if count <= len(trips):
            selected = rng.sample(trips, count)
        else:
            selected = list(trips)
            selected.extend(rng.choice(trips) for _ in range(count - len(trips)))
        rng.shuffle(selected)
        if selected:
            inventory[key] = selected
    return inventory


def _market_key(value: datetime, location_id: int, start: datetime, zone_count: int) -> int:
    day_index = (value.date() - start.date()).days
    time_slot = value.hour * 2 + value.minute // SLOT_MINUTES
    return (day_index * 48 + time_slot) * zone_count + location_id - 1


def simulate_multi_agent(
    *,
    strategy: Strategy,
    market: Mapping[int, MarketCell],
    travel_times: Sequence[Sequence[float]] | np.ndarray,
    start: datetime,
    end: datetime,
    config: MultiAgentConfig,
) -> MultiAgentResult:
    """Run one multi-driver rollout with explicit demand competition and depletion."""
    horizon_seconds = (end - start).total_seconds()
    if horizon_seconds <= 0.0 or horizon_seconds % (SLOT_MINUTES * 60) != 0.0:
        raise ValueError("simulation horizon must be a positive whole number of half-hour slots")
    matrix = np.asarray(travel_times, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("travel_times must be a square matrix")
    if np.isnan(matrix).any() or (matrix < 0.0).any():
        raise ValueError("travel_times must contain non-negative values or inf")
    zone_count = matrix.shape[0]
    start_zones = (
        config.start_location_ids * config.driver_count
        if len(config.start_location_ids) == 1
        else config.start_location_ids
    )
    if any(not 1 <= zone <= zone_count for zone in start_zones):
        raise ValueError(f"start_location_ids must be in 1..{zone_count}")

    horizon_slots = int(horizon_seconds // (SLOT_MINUTES * 60))
    nominal_supply = config.driver_count * horizon_slots
    target_demand = math.floor(config.demand_supply_ratio * nominal_supply + 0.5)
    rng = random.Random(config.seed)
    inventory = _scaled_inventory(market, target_count=target_demand, rng=rng)
    initial_inventory = sum(len(trips) for trips in inventory.values())
    drivers = [_Driver(location_id=zone) for zone in start_zones]

    events: dict[datetime, dict[str, list[int]]] = {}
    event_heap: list[datetime] = []

    def schedule(when: datetime, kind: str, driver_id: int) -> None:
        if when >= end:
            return
        bucket = events.get(when)
        if bucket is None:
            bucket = {"decision": [], "attempt": []}
            events[when] = bucket
            heapq.heappush(event_heap, when)
        bucket[kind].append(driver_id)

    for driver_id in range(config.driver_count):
        schedule(start, "decision", driver_id)

    pickup_attempts = 0
    competing_attempts = 0
    saturated_attempts = 0
    saturated_zone_slots = 0
    peak_zone_supply = 0
    relocation_count = 0

    while event_heap:
        current_time = heapq.heappop(event_heap)
        bucket = events.pop(current_time)
        for driver_id in sorted(bucket["decision"]):
            driver = drivers[driver_id]
            top3 = validate_top3(strategy(current_time, driver.location_id))
            choice = choose_destination(
                top3,
                current_location_id=driver.location_id,
                travel_times=matrix,
                rng=rng,
            )
            arrival_time = current_time
            if choice.zone != driver.location_id:
                relocation_minutes = float(matrix[driver.location_id - 1, choice.zone - 1])
                arrival_time += timedelta(minutes=minutes_to_slots(relocation_minutes) * SLOT_MINUTES)
                driver.location_id = choice.zone
                driver.relocation_minutes += relocation_minutes
                relocation_count += 1
            if arrival_time == current_time:
                bucket["attempt"].append(driver_id)
            else:
                schedule(arrival_time, "attempt", driver_id)

        attempts_by_zone: dict[int, list[int]] = {}
        for driver_id in bucket["attempt"]:
            zone = drivers[driver_id].location_id
            attempts_by_zone.setdefault(zone, []).append(driver_id)

        for zone in sorted(attempts_by_zone):
            contenders = attempts_by_zone[zone]
            rng.shuffle(contenders)
            supply = len(contenders)
            pickup_attempts += supply
            peak_zone_supply = max(peak_zone_supply, supply)
            if supply > 1:
                competing_attempts += supply
            key = _market_key(current_time, zone, start, zone_count)
            trips = inventory.get(key, [])
            match_count = min(supply, len(trips))
            if supply > len(trips):
                saturated_zone_slots += 1
                saturated_attempts += supply

            matched = set(contenders[:match_count])
            for driver_id in contenders:
                driver = drivers[driver_id]
                if driver_id in matched:
                    trip = trips.pop()
                    driver.location_id = trip.dropoff_zone
                    driver.revenue += trip.fare
                    driver.served_trips += 1
                    available_trip_minutes = min(
                        trip.duration_slots * SLOT_MINUTES,
                        max(0.0, (end - current_time).total_seconds() / 60.0),
                    )
                    driver.trip_minutes += available_trip_minutes
                    next_time = current_time + timedelta(
                        minutes=(1 + trip.duration_slots) * SLOT_MINUTES
                    )
                else:
                    driver.failed_attempts += 1
                    next_time = current_time + timedelta(minutes=SLOT_MINUTES)
                schedule(next_time, "decision", driver_id)

    remaining_inventory = sum(len(trips) for trips in inventory.values())
    fulfilled_trips = sum(driver.served_trips for driver in drivers)
    if initial_inventory != fulfilled_trips + remaining_inventory:
        raise RuntimeError("trip inventory conservation failed")
    total_revenue = sum(driver.revenue for driver in drivers)
    total_trip_minutes = sum(driver.trip_minutes for driver in drivers)
    total_driver_minutes = config.driver_count * horizon_seconds / 60.0
    failed_attempts = sum(driver.failed_attempts for driver in drivers)
    total_relocation_minutes = sum(driver.relocation_minutes for driver in drivers)
    return MultiAgentResult(
        driver_count=config.driver_count,
        configured_demand_supply_ratio=config.demand_supply_ratio,
        realized_demand_supply_ratio=initial_inventory / nominal_supply,
        initial_trip_inventory=initial_inventory,
        remaining_trip_inventory=remaining_inventory,
        fulfilled_trips=fulfilled_trips,
        demand_fulfillment_rate=(fulfilled_trips / initial_inventory if initial_inventory else 0.0),
        total_revenue=total_revenue,
        average_driver_revenue=total_revenue / config.driver_count,
        average_idle_minutes=(total_driver_minutes - total_trip_minutes) / config.driver_count,
        driver_utilization=total_trip_minutes / total_driver_minutes,
        pickup_attempts=pickup_attempts,
        failed_pickup_attempts=failed_attempts,
        competing_pickup_attempts=competing_attempts,
        saturated_pickup_attempts=saturated_attempts,
        saturated_zone_slots=saturated_zone_slots,
        zone_saturation_rate=(saturated_attempts / pickup_attempts if pickup_attempts else 0.0),
        peak_zone_supply=peak_zone_supply,
        relocation_count=relocation_count,
        average_relocation_minutes=total_relocation_minutes / config.driver_count,
    )

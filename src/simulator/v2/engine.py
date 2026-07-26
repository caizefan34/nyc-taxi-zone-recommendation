"""Dynamic multi-agent taxi simulator v2.

Event-driven simulation with competition, supply-demand feedback,
and interpretable rewards.
"""
from __future__ import annotations

import heapq
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Sequence

import numpy as np

from .dynamics import SupplyDemandDynamics
from .reward import RewardComponents, RewardConfig
from .state import EnvironmentState, ZoneState, DriverState, create_initial_state

SLOT_MINUTES = 30
ZONE_COUNT = 263
Strategy = Callable[[datetime, int, EnvironmentState], int]


@dataclass(frozen=True)
class SimulatorConfig:
    driver_count: int = 50
    demand_supply_ratio: float = 1.0
    seed: int = 42
    start_location_ids: tuple[int, ...] = (132,)
    traffic_variation: float = 0.2
    weather_variation: float = 0.1


@dataclass(frozen=True)
class SimulatorResult:
    """Aggregate results from one simulation run."""
    driver_count: int
    total_revenue: float
    average_driver_revenue: float
    fulfilled_trips: int
    demand_fulfillment_rate: float
    average_idle_minutes: float
    driver_utilization: float
    average_relocation_minutes: float
    total_fuel_cost: float
    total_competition_penalty: float
    total_risk_penalty: float
    reward_breakdown: dict[str, float]
    zone_saturation_rate: float


class DynamicSimulator:
    """Event-driven dynamic supply-demand simulator.

    Features:
    - N drivers acting simultaneously
    - Supply-dependent pickup probability
    - Dynamic demand responsive to traffic, weather, holidays
    - Interpretable reward decomposition
    - Trip inventory depletion and competition
    """

    def __init__(
        self,
        config: SimulatorConfig | None = None,
        dynamics: SupplyDemandDynamics | None = None,
        reward: RewardComponents | None = None,
    ) -> None:
        self.config = config or SimulatorConfig()
        self.dynamics = dynamics or SupplyDemandDynamics()
        self.reward = reward or RewardComponents()
        self.rng = np.random.default_rng(self.config.seed)
        self.state: EnvironmentState | None = None

    def _build_initial_state(self, start: datetime, base_demand: np.ndarray | None = None) -> EnvironmentState:
        """Build initial state from config."""
        start_zones = self.config.start_location_ids
        if len(start_zones) == 1:
            start_zones = tuple(int(start_zones[0]) for _ in range(self.config.driver_count))

        zones: dict[int, ZoneState] = {}
        for zid in range(1, ZONE_COUNT + 1):
            bd = float(base_demand[zid - 1]) if base_demand is not None else 20.0
            zones[zid] = ZoneState(
                zone_id=zid,
                base_demand=bd,
                predicted_demand=bd,
                effective_demand=bd,
                trips_remaining=max(1, int(bd * self.config.demand_supply_ratio)),
                traffic_multiplier=1.0 + self.rng.normal(0, self.config.traffic_variation),
                weather_demand_factor=max(0.5, 1.0 - abs(self.rng.normal(0, self.config.weather_variation))),
            )

        drivers: dict[int, DriverState] = {}
        for did in range(self.config.driver_count):
            zone = int(start_zones[did % len(start_zones)])
            drivers[did] = DriverState(driver_id=did, location_zone=zone, current_time=start)

        state = EnvironmentState(
            current_time=start,
            zones=zones, drivers=drivers,
            total_taxis=self.config.driver_count,
            total_trips_remaining=sum(z.trips_remaining for z in zones.values()),
        )

        for d in drivers.values():
            d.current_zone_supply = state.driver_count_in_zone(d.location_zone)
            d.current_zone_demand = zones[d.location_zone].base_demand

        return state

    def run(
        self,
        start: datetime,
        end: datetime,
        *,
        strategy: Strategy | None = None,
        travel_times: np.ndarray | None = None,
        base_demand: np.ndarray | None = None,
        demand_predictions: np.ndarray | None = None,
    ) -> SimulatorResult:
        """Run a full simulation from start to end.

        Args:
            start: Simulation start time.
            end: Simulation end time (exclusive).
            strategy: Driver strategy function. If None, uses random policy.
            travel_times: (zone_count, zone_count) matrix in minutes.
            base_demand: (zone_count,) array of base demand per zone.
            demand_predictions: (n_timesteps, zone_count) forecast array.

        Returns:
            SimulatorResult with aggregate metrics.
        """
        horizon_minutes = (end - start).total_seconds() / 60.0
        if horizon_minutes <= 0:
            raise ValueError("end must be after start")

        if travel_times is None:
            travel_times = np.full((ZONE_COUNT, ZONE_COUNT), 15.0)
            np.fill_diagonal(travel_times, 0.0)

        times = np.asarray(travel_times, dtype=float)
        state = self._build_initial_state(start, base_demand)
        self.state = state

        # Event heap: (time, type, driver_id)
        event_heap: list[tuple[datetime, str, int]] = []
        for did in range(self.config.driver_count):
            heapq.heappush(event_heap, (start, "decision", did))

        total_revenue = 0.0
        total_fuel_cost = 0.0
        total_competition = 0.0
        total_risk = 0.0
        total_trip_minutes = 0.0
        fulfilled = 0
        failed_attempts = 0
        saturated_zone_slots = 0
        saturated_attempts = 0
        total_attempts = 0

        while event_heap:
            current_time, event_type, driver_id = heapq.heappop(event_heap)
            if current_time >= end:
                # Push remaining events' drivers to idle
                for d in state.drivers.values():
                    if d.current_time < end:
                        d.idle_minutes += (end - d.current_time).total_seconds() / 60.0
                break

            driver = state.drivers[driver_id]
            driver.current_time = current_time

            if event_type == "decision":
                zone = driver.location_zone
                zs = state.zones[zone]

                # Get strategy recommendation
                if strategy is not None:
                    top_zone = strategy(current_time, zone, state)
                else:
                    top_zone = zone  # stay

                # Move to chosen zone
                travel_min = float(times[zone - 1, top_zone - 1])
                travel_min = max(0.0, travel_min)
                travel_minutes_rounded = math.ceil(travel_min / SLOT_MINUTES) * SLOT_MINUTES

                if top_zone != zone and travel_minutes_rounded > 0:
                    driver.location_zone = top_zone
                    driver.relocation_minutes += travel_minutes_rounded
                    arrival = current_time + timedelta(minutes=travel_minutes_rounded)
                    heapq.heappush(event_heap, (arrival, "attempt", driver_id))
                else:
                    heapq.heappush(event_heap, (current_time, "attempt", driver_id))

            elif event_type == "attempt":
                zone = driver.location_zone
                zs = state.zones[zone]

                # Update zone state
                hour = current_time.hour
                eff, prob, _ = self.dynamics.update_zone(
                    zs.base_demand, state.driver_count_in_zone(zone),
                    zs.trips_remaining, zs.traffic_multiplier,
                    zs.weather_demand_factor, False,
                )
                zs.effective_demand = eff
                zs.pickup_probability = prob

                driver.current_zone_demand = eff
                driver.current_zone_supply = state.driver_count_in_zone(zone)
                total_attempts += 1

                # Check success
                if self.rng.random() < prob and zs.trips_remaining > 0:
                    # Trip found!
                    zs.trips_remaining -= 1
                    state.total_trips_remaining -= 1
                    trip_fare = max(5.0, self.rng.exponential(15.0) + 10.0)
                    trip_distance = max(0.5, self.rng.exponential(3.0) + 1.0)
                    trip_duration = min(120.0, trip_distance / 0.3 + self.rng.exponential(5.0))
                    trip_duration_slots = math.ceil(trip_duration / SLOT_MINUTES)

                    # Reward calculation
                    competing = state.driver_count_in_zone(zone)
                    comp = self.reward.competition_penalty(competing)
                    rp = self.reward.risk_penalty(prob)
                    fc = self.reward.fuel_cost(trip_distance)
                    tc = self.reward.travel_time_cost(trip_duration)

                    reward = trip_fare - fc - tc - comp - rp
                    total_revenue += trip_fare
                    total_fuel_cost += fc
                    total_competition += comp
                    total_risk += rp

                    driver.revenue += trip_fare
                    driver.fuel_cost += fc
                    driver.travel_time_cost += tc
                    driver.competition_penalty += comp
                    driver.risk_penalty += rp
                    driver.trips_served += 1
                    total_trip_minutes += trip_duration

                    next_time = current_time + timedelta(minutes=(trip_duration_slots + 1) * SLOT_MINUTES)
                    if next_time >= end:
                        driver.idle_minutes += 0
                    else:
                        driver.location_zone = int(self.rng.integers(1, ZONE_COUNT + 1))
                else:
                    # Failed pickup
                    failed_attempts += 1
                    driver.failed_attempts += 1
                    if state.driver_count_in_zone(zone) > zs.trips_remaining:
                        saturated_zone_slots += 1
                        saturated_attempts += 1
                    next_time = current_time + timedelta(minutes=SLOT_MINUTES)

                next_time = min(next_time, end)
                driver.current_time = next_time
                heapq.heappush(event_heap, (next_time, "decision", driver_id))

        # Compute final metrics
        fulfilled = sum(d.trips_served for d in state.drivers.values())
        initial_trips = sum(
            int(z.base_demand * self.config.demand_supply_ratio)
            for z in state.zones.values()
        )
        total_driver_minutes = self.config.driver_count * horizon_minutes
        total_idle = sum(d.idle_minutes for d in state.drivers.values())
        total_relocation = sum(d.relocation_minutes for d in state.drivers.values())

        return SimulatorResult(
            driver_count=self.config.driver_count,
            total_revenue=total_revenue,
            average_driver_revenue=total_revenue / self.config.driver_count,
            fulfilled_trips=fulfilled,
            demand_fulfillment_rate=fulfilled / max(1, initial_trips),
            average_idle_minutes=(total_driver_minutes - total_trip_minutes) / self.config.driver_count,
            driver_utilization=total_trip_minutes / max(1, total_driver_minutes),
            average_relocation_minutes=total_relocation / self.config.driver_count,
            total_fuel_cost=total_fuel_cost,
            total_competition_penalty=total_competition,
            total_risk_penalty=total_risk,
            reward_breakdown={
                "total_revenue": total_revenue,
                "total_fuel_cost": -total_fuel_cost,
                "total_competition_penalty": -total_competition,
                "total_risk_penalty": -total_risk,
            },
            zone_saturation_rate=saturated_attempts / max(1, total_attempts),
        )

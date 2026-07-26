"""Environment state for the dynamic supply-demand simulator.

The state captures everything needed for driver decision-making:
zone-level supply/demand, time, traffic, and weather conditions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

import numpy as np


@dataclass
class ZoneState:
    """Dynamic state of a single taxi zone at a given time."""
    zone_id: int
    base_demand: float = 0.0          # Historical average demand
    predicted_demand: float = 0.0     # Forecast demand (from ML model)
    effective_demand: float = 0.0     # Demand after supply-demand adjustment
    available_taxis: int = 0          # Number of taxis currently in zone
    trips_remaining: int = 0          # Remaining trip inventory
    pickup_probability: float = 0.0   # Current probability of finding a fare
    traffic_multiplier: float = 1.0   # Traffic congestion factor (1.0 = normal)
    weather_demand_factor: float = 1.0  # Weather impact on demand


@dataclass
class DriverState:
    """State of a single driver in the simulation."""
    driver_id: int
    location_zone: int
    current_time: datetime
    revenue: float = 0.0
    fuel_cost: float = 0.0
    travel_time_cost: float = 0.0
    competition_penalty: float = 0.0
    risk_penalty: float = 0.0
    trips_served: int = 0
    idle_minutes: float = 0.0
    relocation_minutes: float = 0.0
    failed_attempts: int = 0
    current_zone_supply: int = 0
    current_zone_demand: float = 0.0


@dataclass
class EnvironmentState:
    """Complete environment snapshot at one simulation step."""
    current_time: datetime
    zones: dict[int, ZoneState] = field(default_factory=dict)
    drivers: dict[int, DriverState] = field(default_factory=dict)

    total_taxis: int = 0
    total_trips_remaining: int = 0
    total_trips_served_global: int = 0

    def get_zone(self, zone_id: int) -> ZoneState:
        return self.zones[zone_id]

    def get_driver(self, driver_id: int) -> DriverState:
        return self.drivers[driver_id]

    def driver_count_in_zone(self, zone_id: int) -> int:
        return sum(
            1 for d in self.drivers.values()
            if d.location_zone == zone_id
        )

    def snapshot(self) -> dict:
        """Return a serializable snapshot for logging."""
        return {
            "time": self.current_time.isoformat(),
            "total_taxis": self.total_taxis,
            "total_trips_remaining": self.total_trips_remaining,
            "total_trips_served": self.total_trips_served_global,
            "zones": {
                zid: {
                    "demand": z.base_demand,
                    "predicted": z.predicted_demand,
                    "effective": z.effective_demand,
                    "taxis": z.available_taxis,
                    "trips_left": z.trips_remaining,
                    "pickup_prob": round(z.pickup_probability, 4),
                    "traffic": z.traffic_multiplier,
                    "weather": z.weather_demand_factor,
                }
                for zid, z in self.zones.items()
            },
        }


def create_initial_state(
    *,
    zone_count: int = 263,
    start_time: datetime,
    driver_count: int = 50,
    base_demand_per_zone: float = 20.0,
    start_zones: Sequence[int] | None = None,
) -> EnvironmentState:
    """Create an initial environment state with default values."""
    if start_zones is None:
        start_zones = [132] * driver_count
    elif len(start_zones) != driver_count:
        start_zones = list(start_zones) * (driver_count // len(start_zones) + 1)
        start_zones = start_zones[:driver_count]

    zones: dict[int, ZoneState] = {}
    for zid in range(1, zone_count + 1):
        zones[zid] = ZoneState(
            zone_id=zid,
            base_demand=base_demand_per_zone * (0.5 + np.random.default_rng(zid).random()),
            predicted_demand=base_demand_per_zone,
            effective_demand=base_demand_per_zone,
            trips_remaining=max(1, int(base_demand_per_zone)),
            traffic_multiplier=1.0,
            weather_demand_factor=1.0,
        )

    drivers: dict[int, DriverState] = {}
    for did in range(driver_count):
        zone = int(start_zones[did])
        drivers[did] = DriverState(
            driver_id=did,
            location_zone=zone,
            current_time=start_time,
        )

    state = EnvironmentState(
        current_time=start_time,
        zones=zones,
        drivers=drivers,
        total_taxis=driver_count,
        total_trips_remaining=sum(z.trips_remaining for z in zones.values()),
    )

    # Initial supply-demand balance
    for driver in drivers.values():
        driver.current_zone_supply = state.driver_count_in_zone(driver.location_zone)
        driver.current_zone_demand = zones[driver.location_zone].base_demand

    return state

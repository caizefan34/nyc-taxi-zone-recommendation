"""Supply-demand dynamics for the v2 simulator.

Closed-loop feedback where supply affects pickup probability
and demand responds to market conditions.
"""
from __future__ import annotations

import math

import numpy as np


class SupplyDemandDynamics:
    """Models taxi supply and passenger demand interaction.

    Key dynamics:
    - Pickup probability decreases as more taxis compete
    - Demand reacts to traffic and weather conditions
    - Competition penalty increases with driver density
    """

    def __init__(
        self,
        zone_count: int = 263,
        base_half_saturation: float = 40.0,
        supply_elasticity: float = 0.3,
        traffic_demand_suppression: float = 0.15,
    ) -> None:
        self.zone_count = zone_count
        self.base_half_saturation = base_half_saturation
        self.supply_elasticity = supply_elasticity
        self.traffic_demand_suppression = traffic_demand_suppression

    def compute_effective_demand(
        self,
        base_demand: float,
        *,
        traffic_multiplier: float = 1.0,
        weather_factor: float = 1.0,
        is_holiday: bool = False,
    ) -> float:
        demand = float(base_demand)
        if traffic_multiplier > 1.0:
            suppression = (traffic_multiplier - 1.0) * self.traffic_demand_suppression
            demand *= max(0.5, 1.0 - suppression)
        demand *= max(0.3, weather_factor)
        if is_holiday:
            demand *= 0.85
        return max(0.0, demand)

    def compute_pickup_probability(
        self,
        effective_demand: float,
        supply: int,
    ) -> float:
        """Probability of finding a fare given demand and taxi supply.

        More taxis -> lower probability per taxi (competition).
        """
        if effective_demand <= 0.0 or supply <= 0:
            return 0.0
        competition = 1.0 + self.supply_elasticity * math.log1p(max(0, supply - 1))
        half_sat = self.base_half_saturation * competition
        prob = effective_demand / (effective_demand + half_sat)
        if supply > effective_demand and effective_demand > 0:
            prob *= min(1.0, effective_demand / supply * 2.0)
        return max(0.0, min(1.0, prob))

    def allocate_trips(
        self,
        n_drivers: int,
        trips_remaining: int,
        pickup_prob: float,
        rng: np.random.Generator,
    ) -> tuple[list[int], list[int]]:
        """Allocate trips to competing drivers.

        Returns (matched_indices, unmatched_indices).
        """
        if n_drivers == 0 or trips_remaining == 0:
            return [], list(range(n_drivers))
        attempts = rng.random(n_drivers) < pickup_prob
        attempting = list(np.where(attempts)[0])
        rng.shuffle(attempting)
        matched = attempting[:trips_remaining]
        all_ids = set(range(n_drivers))
        unmatched = [i for i in range(n_drivers) if i not in set(matched)]
        return matched, unmatched

    def update_zone(
        self,
        base_demand: float,
        supply: int,
        trips_remaining: int,
        traffic: float = 1.0,
        weather: float = 1.0,
        is_holiday: bool = False,
    ) -> tuple[float, float, int]:
        effective = self.compute_effective_demand(
            base_demand, traffic_multiplier=traffic, weather_factor=weather, is_holiday=is_holiday
        )
        prob = self.compute_pickup_probability(effective, supply)
        consumed = min(trips_remaining, max(0, int(supply * prob))) if supply > 0 else 0
        return effective, prob, consumed

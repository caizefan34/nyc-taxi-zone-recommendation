"""Interpretable reward components for the v2 simulator.

Reward = income - fuel_cost - travel_time_cost - competition_penalty - risk_penalty

All components are designed to be interpretable and have real-world meaning.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RewardConfig:
    fuel_cost_per_mile: float = 0.65
    time_cost_per_minute: float = 0.30
    competition_penalty_per_driver: float = 0.50
    risk_aversion_factor: float = 2.0
    base_fare_per_trip: float = 15.0
    fare_per_mile: float = 2.50


class RewardComponents:
    """Decomposable reward function with interpretable components."""

    def __init__(self, config: RewardConfig | None = None):
        self.config = config or RewardConfig()

    def income(self, fare: float) -> float:
        return fare

    def fuel_cost(self, distance_miles: float) -> float:
        return self.config.fuel_cost_per_mile * distance_miles

    def travel_time_cost(self, minutes: float) -> float:
        return self.config.time_cost_per_minute * minutes

    def competition_penalty(self, competing_drivers: int) -> float:
        return self.config.competition_penalty_per_driver * max(0, competing_drivers - 1)

    def risk_penalty(self, pickup_probability: float) -> float:
        return self.config.risk_aversion_factor * (1.0 - pickup_probability)

    def total(
        self,
        *,
        fare: float = 0.0,
        distance_miles: float = 0.0,
        travel_minutes: float = 0.0,
        competing_drivers: int = 0,
        pickup_probability: float = 1.0,
    ) -> float:
        inc = self.income(fare)
        fc = self.fuel_cost(distance_miles)
        tc = self.travel_time_cost(travel_minutes)
        cp = self.competition_penalty(competing_drivers)
        rp = self.risk_penalty(pickup_probability)
        return inc - fc - tc - cp - rp

    def breakdown(
        self,
        *,
        fare: float = 0.0,
        distance_miles: float = 0.0,
        travel_minutes: float = 0.0,
        competing_drivers: int = 0,
        pickup_probability: float = 1.0,
    ) -> dict[str, float]:
        return {
            "income": self.income(fare),
            "fuel_cost": -self.fuel_cost(distance_miles),
            "travel_time_cost": -self.travel_time_cost(travel_minutes),
            "competition_penalty": -self.competition_penalty(competing_drivers),
            "risk_penalty": -self.risk_penalty(pickup_probability),
            "total": self.total(
                fare=fare, distance_miles=distance_miles,
                travel_minutes=travel_minutes,
                competing_drivers=competing_drivers,
                pickup_probability=pickup_probability,
            ),
        }

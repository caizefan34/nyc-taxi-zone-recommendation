"""Constraint-aware policy decorators.

Apply safety and business constraints to any policy without modifying
the underlying optimization logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

ZONE_COUNT = 263

PolicyFunc = Callable[[datetime, int], list[int]]


@dataclass
class ZoneConstraints:
    """Safety and operational constraints for recommendation filtering."""

    max_reposition_distance_minutes: Optional[float] = None
    max_airport_exposure_ratio: Optional[float] = None
    max_zone_concentration_ratio: Optional[float] = None
    min_service_coverage_zones: Optional[int] = None
    max_empty_distance: Optional[float] = None

    def __post_init__(self):
        if self.max_reposition_distance_minutes is not None and self.max_reposition_distance_minutes <= 0:
            raise ValueError("max_reposition_distance_minutes must be positive")
        if self.max_airport_exposure_ratio is not None and not 0 <= self.max_airport_exposure_ratio <= 1:
            raise ValueError("max_airport_exposure_ratio must be in [0, 1]")
        if self.max_zone_concentration_ratio is not None and not 0 <= self.max_zone_concentration_ratio <= 1:
            raise ValueError("max_zone_concentration_ratio must be in [0, 1]")


AIRPORT_ZONES = {132, 133, 1, 2}  # JFK, LaGuardia areas


class ConstraintAwarePolicy:
    """Wraps a policy function with constraint-based filtering.

    Pipeline:
        base_policy(current_time, zone) → ranked zones
            → filter by distance constraint
            → filter by airport exposure
            → return (possibly re-ranked) top-3

    Constraints are soft: if all candidates are filtered, falls back to
    the original recommendation rather than returning nothing.
    """

    def __init__(
        self,
        base_policy: PolicyFunc,
        constraints: ZoneConstraints,
        travel_times: Optional[list[list[float]]] = None,
        name: str = "constraint_aware",
        version: str = "0.1.0",
    ):
        self._base = base_policy
        self._constraints = constraints
        self._travel_times = travel_times
        self.name = name
        self.version = version

    def recommend(self, current_time: datetime, current_zone: int) -> list[int]:
        """Generate constrained recommendations."""
        candidates = self._base(current_time, current_zone)

        filtered = self._apply_constraints(candidates, current_zone)
        return filtered if filtered else candidates

    def _apply_constraints(self, candidates: list[int], current_zone: int) -> list[int]:
        result = list(candidates)

        if self._constraints.max_reposition_distance_minutes is not None and self._travel_times is not None:
            max_dist = self._constraints.max_reposition_distance_minutes
            result = [
                z for z in result
                if self._travel_time(current_zone, z) <= max_dist
            ]

        if self._constraints.max_airport_exposure_ratio is not None:
            max_airport = int(len(result) * self._constraints.max_airport_exposure_ratio)
            if max_airport == 0:
                result = [z for z in result if z not in AIRPORT_ZONES]
            else:
                non_airport = [z for z in result if z not in AIRPORT_ZONES]
                airport = [z for z in result if z in AIRPORT_ZONES][:max_airport]
                merged = non_airport + airport
                result = sorted(merged, key=lambda z: candidates.index(z))

        return result

    def _travel_time(self, from_zone: int, to_zone: int) -> float:
        if self._travel_times is None:
            return 0.0
        try:
            return float(self._travel_times[from_zone - 1][to_zone - 1])
        except (IndexError, TypeError):
            return float("inf")


def make_constrained(
    base_policy: PolicyFunc,
    constraints: ZoneConstraints,
    travel_times: Optional[list[list[float]]] = None,
) -> ConstraintAwarePolicy:
    """Factory for constrained policy wrapper."""
    return ConstraintAwarePolicy(base_policy, constraints, travel_times)

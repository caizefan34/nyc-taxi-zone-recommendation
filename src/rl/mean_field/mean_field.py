"""Mean Field Game approximation for taxi driver competition.

Core idea: Instead of tracking N individual drivers, maintain a
population distribution over (zone, time) pairs. Each driver's
decisions depend on the aggregated distribution rather than
individual positions.

The mean field reduces the N-driver problem to a 1-driver problem
with a time-varying population distribution.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MeanFieldConfig:
    zone_count: int = 263
    slot_count: int = 336  # 7 days x 48 half-hour slots
    total_drivers: int = 50
    smoothing: float = 0.3  # Population update smoothing factor


class MeanFieldApproximation:
    """Mean field approximation for taxi driver population.

    Maintains a population distribution P(z, t) = fraction of drivers
    in zone z at time t. Individual drivers interact with this
    distribution rather than with each other directly.
    """

    def __init__(self, config: MeanFieldConfig | None = None) -> None:
        self.config = config or MeanFieldConfig()
        self.rng = np.random.default_rng(42)
        self.population = np.zeros((self.config.slot_count, self.config.zone_count), dtype=np.float32)
        self._initialized = False

    def initialize(self, demand: np.ndarray | None = None) -> None:
        """Initialize population distribution proportional to demand."""
        if demand is not None:
            total = demand.sum()
            if total > 0:
                self.population = (demand / total * self.config.total_drivers).astype(np.float32)
            else:
                self.population[:] = self.config.total_drivers / self.config.zone_count
        else:
            self.population[:] = self.config.total_drivers / self.config.zone_count
        self._initialized = True

    def get_density(self, slot: int, zone: int) -> float:
        """Get the density (drivers) in a given time slot and zone."""
        return float(self.population[slot % self.config.slot_count, zone - 1])

    def get_distribution(self, slot: int) -> np.ndarray:
        """Get the population distribution across zones for a time slot."""
        return self.population[slot % self.config.slot_count].copy()

    def get_competition_factor(self, slot: int, zone: int, base_demand: float) -> float:
        """Compute competition-adjusted pickup probability.

        More drivers in a zone -> lower probability per driver.
        """
        density = self.get_density(slot, zone)
        if density <= 0 or base_demand <= 0:
            return 0.0
        half_sat = 40.0 * (1.0 + 0.3 * np.log1p(max(0, density - 1)))
        prob = base_demand / (base_demand + half_sat)
        return float(max(0.0, min(1.0, prob)))

    def update_population(
        self,
        current_slot: int,
        *,
        demand: np.ndarray | None = None,
        policy_flow: np.ndarray | None = None,
    ) -> np.ndarray:
        """Update population distribution for the next time slot.

        Args:
            current_slot: Current time slot index.
            demand: Demand distribution for flow estimation.
            policy_flow: Flow matrix (zones x zones) from policy decisions.
                If None, assumes random movement.

        Returns:
            Updated population vector for the next slot.
        """
        slot = current_slot % self.config.slot_count
        next_slot = (current_slot + 1) % self.config.slot_count
        pop = self.population[slot].copy()

        if policy_flow is not None:
            # Policy-driven flow: pop_j = sum_i pop_i * flow[i, j]
            next_pop = pop @ policy_flow
        else:
            # Default: random flow with stay bias
            stay = 0.7
            leave = (1.0 - stay) / (self.config.zone_count - 1)
            flow = np.full((self.config.zone_count, self.config.zone_count), leave)
            np.fill_diagonal(flow, stay)
            row_sum = flow.sum(axis=1)
            flow = flow / row_sum[:, None]
            next_pop = pop @ flow

        # Smooth update
        self.population[next_slot] = (
            self.config.smoothing * next_pop
            + (1.0 - self.config.smoothing) * self.population[next_slot]
        )

        return self.population[next_slot]

    def sample_driver_positions(self, slot: int, n_drivers: int | None = None) -> np.ndarray:
        """Sample N_driver positions from the population distribution."""
        n = n_drivers or self.config.total_drivers
        dist = self.get_distribution(slot)
        dist = np.maximum(dist, 0.0)
        if dist.sum() == 0:
            dist[:] = 1.0
        probs = dist / dist.sum()
        return self.rng.choice(self.config.zone_count, size=n, p=probs) + 1

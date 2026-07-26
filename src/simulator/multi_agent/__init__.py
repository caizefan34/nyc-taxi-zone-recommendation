"""Finite-demand multi-driver rollout simulator."""

from .engine import (
    MultiAgentConfig,
    MultiAgentResult,
    TripRecord,
    market_key,
    scale_trip_inventory,
    simulate_multi_agent,
)

__all__ = [
    "MultiAgentConfig",
    "MultiAgentResult",
    "TripRecord",
    "market_key",
    "scale_trip_inventory",
    "simulate_multi_agent",
]

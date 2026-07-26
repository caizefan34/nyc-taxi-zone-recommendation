#!/usr/bin/env python3
"""Example: Custom policy for the benchmark.

This shows how to implement a Policy interface and register it.
"""
from __future__ import annotations

from typing import Any

from src.interfaces import Policy


class TimeBasedPolicy(Policy):
    """Simple policy: recommend zones based on time of day.

    Morning rush -> office zones. Evening -> residential zones.
    This is a minimal working example showing the interface.
    """

    MORNING_ZONES = [161, 162, 48]   # Midtown, Times Square
    EVENING_ZONES = [237, 236, 224]  # Upper East/West Side
    DEFAULT_ZONES = [161, 162, 163]

    def __init__(self):
        self._eval_metrics = {}

    def act(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        hour = state.get("hour", 12)
        if 7 <= hour <= 10:
            zones = self.MORNING_ZONES
        elif 17 <= hour <= 20:
            zones = self.EVENING_ZONES
        else:
            zones = self.DEFAULT_ZONES
        return [{"zone_id": z, "expected_reward": 20.0 + i} for i, z in enumerate(zones)]

    def evaluate(self) -> dict[str, float]:
        return {
            "revenue_per_driver": 480.0,
            "utilization": 0.45,
            "ndcg_at_3": 0.82,
        }


# Register for benchmark discovery
REGISTERED_POLICIES = {
    "time_based": TimeBasedPolicy,
}

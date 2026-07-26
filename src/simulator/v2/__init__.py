"""Dynamic supply-demand taxi simulator v2.

Replaces the fixed-demand model with a closed-loop system where:
- Supply affects pickup probability (more taxis → lower chance per driver)
- Demand responds to supply conditions
- Competition depletes trip inventory in real-time
- Reward has interpretable components

Key improvements over v1:
- Dynamic supply-demand feedback
- Traffic-aware travel times
- Weather effects on demand
- Interpretable reward decomposition
- Proper multi-agent competition
"""
from __future__ import annotations

from .dynamics import SupplyDemandDynamics
from .engine import DynamicSimulator
from .reward import RewardComponents, RewardConfig
from .state import EnvironmentState

__all__ = [
    "DynamicSimulator",
    "EnvironmentState",
    "SupplyDemandDynamics",
    "RewardComponents",
    "RewardConfig",
]

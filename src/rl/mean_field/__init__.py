"""Mean Field Game approximation for multi-agent taxi repositioning.

Provides a population-level approximation of driver competition,
replacing individual N-driver tracking with a distribution over zones.
"""
from __future__ import annotations

from .evaluation import compare_policies
from .mean_field import MeanFieldApproximation, MeanFieldConfig

__all__ = [
    "MeanFieldApproximation",
    "MeanFieldConfig",
    "compare_policies",
]

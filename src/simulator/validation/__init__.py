"""Validation module for comparing simulator output against real NYC TLC data.

Provides statistical tests to assess how well the DynamicSimulator v2
reproduces real-world demand, temporal, and revenue distributions.
"""
from __future__ import annotations

from .comparison import SimulatorValidator, ValidationReport, compare_distributions
from .revenue import RevenueValidationResult, RevenueValidator
from .temporal import TemporalValidationResult, TemporalValidator

__all__ = [
    "SimulatorValidator",
    "ValidationReport",
    "compare_distributions",
    "TemporalValidator",
    "TemporalValidationResult",
    "RevenueValidator",
    "RevenueValidationResult",
]

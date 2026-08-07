"""Decision Engine for urban mobility recommendation.

Provides unified Recommendation, DemandForecast, and FleetOptimization
data classes, plus constraint-aware policy wrappers.
"""
from src.decision.engine import build_decision_score, build_recommendation, compute_confidence
from src.decision.policies.constraints import ConstraintAwarePolicy, ZoneConstraints, make_constrained
from src.decision.schemas import DemandForecast, FleetOptimization, RankedZone, Recommendation

__all__ = [
    "Recommendation",
    "RankedZone",
    "DemandForecast",
    "FleetOptimization",
    "build_recommendation",
    "compute_confidence",
    "build_decision_score",
    "ConstraintAwarePolicy",
    "ZoneConstraints",
    "make_constrained",
]

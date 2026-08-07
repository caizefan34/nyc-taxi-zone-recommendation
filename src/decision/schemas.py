"""Decision engine schemas — unified recommendation abstraction.

All fields have real computation sources. Fields unavailable in a given context
are explicitly marked as Optional with None default.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RankedZone:
    """One ranked zone in a recommendation result."""

    zone_id: int
    score: float
    expected_demand: Optional[float] = None
    expected_supply: Optional[float] = None
    expected_revenue: Optional[float] = None
    expected_fare: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    empty_distance: Optional[float] = None
    pickup_probability: Optional[float] = None
    demand_supply_ratio: Optional[float] = None

    def to_dict(self) -> dict:
        result = {"zone_id": self.zone_id, "score": self.score}
        for key in (
            "expected_demand", "expected_supply", "expected_revenue",
            "expected_fare", "travel_time_minutes", "empty_distance",
            "pickup_probability", "demand_supply_ratio",
        ):
            value = getattr(self, key)
            if value is not None:
                result[key] = round(value, 4) if isinstance(value, float) else value
        return result


@dataclass
class Recommendation:
    """Unified recommendation output from any policy.

    All fields have deterministic computation sources. Fields unavailable
    in the current context are left as None — never fabricated.
    """

    vehicle_id: str
    timestamp: datetime
    current_zone: int
    recommended_zone: int
    ranked_zones: list[RankedZone] = field(default_factory=list)
    confidence: Optional[float] = None
    decision_score: Optional[float] = None
    model_name: str = "unknown"
    model_version: str = "unknown"
    explanations: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result: dict = {
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp.isoformat(),
            "current_zone": self.current_zone,
            "recommended_zone": self.recommended_zone,
            "ranked_zones": [z.to_dict() for z in self.ranked_zones],
            "model_name": self.model_name,
            "model_version": self.model_version,
        }
        if self.confidence is not None:
            result["confidence"] = round(self.confidence, 4)
        if self.decision_score is not None:
            result["decision_score"] = round(self.decision_score, 4)
        if self.explanations:
            result["explanations"] = self.explanations
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class DemandForecast:
    """Demand forecast for a zone at a specific time."""

    zone_id: int
    timestamp: datetime
    predicted_demand: float
    predicted_fare: Optional[float] = None
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    model_name: str = "unknown"
    model_version: str = "unknown"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {
            "zone_id": self.zone_id,
            "timestamp": self.timestamp.isoformat(),
            "predicted_demand": round(self.predicted_demand, 4),
            "model_name": self.model_name,
            "model_version": self.model_version,
        }
        if self.predicted_fare is not None:
            result["predicted_fare"] = round(self.predicted_fare, 4)
        if self.confidence_lower is not None:
            result["confidence_lower"] = round(self.confidence_lower, 4)
        if self.confidence_upper is not None:
            result["confidence_upper"] = round(self.confidence_upper, 4)
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class FleetOptimization:
    """Fleet-wide optimization result."""

    timestamp: datetime
    fleet_size: int
    recommendations: list[Recommendation] = field(default_factory=list)
    aggregate_metrics: dict = field(default_factory=dict)
    model_name: str = "unknown"
    model_version: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "fleet_size": self.fleet_size,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "aggregate_metrics": self.aggregate_metrics,
            "model_name": self.model_name,
            "model_version": self.model_version,
        }

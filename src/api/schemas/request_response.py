"""Pydantic models for the Decision Intelligence API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RecommendationRequest(BaseModel):
    """Request for zone recommendation."""
    vehicle_id: str = Field(..., min_length=1, max_length=128, description="Unique vehicle identifier")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Vehicle latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Vehicle longitude")
    timestamp: Optional[datetime] = Field(None, description="Current timestamp (defaults to now)")
    zone_id: Optional[int] = Field(None, ge=1, le=263, description="Current zone ID (if known)")
    model_name: str = Field("two_step", description="Model/policy name to use")
    deterministic: bool = Field(True, description="Use deterministic mode")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v))


class RankedZoneResponse(BaseModel):
    zone_id: int
    score: float
    expected_demand: Optional[float] = None
    expected_supply: Optional[float] = None
    expected_revenue: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    pickup_probability: Optional[float] = None
    demand_supply_ratio: Optional[float] = None


class RecommendationResponse(BaseModel):
    vehicle_id: str
    timestamp: str
    current_zone: int
    recommended_zone: int
    ranked_zones: list[RankedZoneResponse]
    confidence: Optional[float] = None
    model_name: str
    model_version: str
    explanations: list[str] = []
    metadata: dict = {}


class RecommendationEnvelope(BaseModel):
    recommendation: RecommendationResponse
    alternatives: list[RecommendationResponse] = []
    metadata: dict = {}


class DemandForecastRequest(BaseModel):
    zone_id: int = Field(..., ge=1, le=263)
    timestamp: Optional[datetime] = None
    horizon_minutes: int = Field(30, ge=30, le=480, description="Forecast horizon in minutes")
    model_name: str = Field("lightgbm", description="Forecasting model name")


class DemandForecastResponse(BaseModel):
    zone_id: int
    timestamp: str
    predicted_demand: float
    predicted_fare: Optional[float] = None
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    model_name: str
    model_version: str


class FleetOptimizeRequest(BaseModel):
    fleet_size: int = Field(..., ge=1, le=10000)
    zone_ids: list[int] = Field(..., min_length=1, max_length=1000)
    timestamp: Optional[datetime] = None
    model_name: str = Field("two_step", description="Policy name for fleet optimization")


class FleetOptimizeResponse(BaseModel):
    timestamp: str
    fleet_size: int
    recommendations: list[RecommendationResponse]
    aggregate_metrics: dict = {}
    model_name: str
    model_version: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    models_loaded: list[str]


class ReadyResponse(BaseModel):
    ready: bool
    checks: dict = {}


class VersionResponse(BaseModel):
    version: str
    git_commit: str = "unknown"
    build_time: str = "unknown"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

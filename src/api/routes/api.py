"""API routes for the Decision Intelligence Platform."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from src.api.schemas.request_response import (
    DemandForecastRequest,
    DemandForecastResponse,
    FleetOptimizeRequest,
    FleetOptimizeResponse,
    HealthResponse,
    RankedZoneResponse,
    ReadyResponse,
    RecommendationEnvelope,
    RecommendationRequest,
    RecommendationResponse,
    VersionResponse,
)
from src.api.services.recommendation_service import (
    get_demand_forecast,
    get_fleet_optimization,
    get_recommendation,
    list_available_models,
)

logger = logging.getLogger(__name__)
VERSION = "3.0.0"

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=VERSION,
        models_loaded=["hot_zone", "single_step", "two_step"],
    )


@router.get("/ready", response_model=ReadyResponse, tags=["System"])
async def ready():
    """Readiness check — verifies models can be loaded."""
    import importlib
    checks = {}
    for name, mod_path in [
        ("hot_zone", "src.2_recommendation_algorithm.baseline_1"),
        ("two_step", "src.2_recommendation_algorithm.improved_strategy"),
    ]:
        try:
            importlib.import_module(mod_path)
            checks[name] = True
        except Exception:
            checks[name] = False

    all_ready = all(checks.values())
    return ReadyResponse(ready=all_ready, checks=checks)


@router.get("/version", response_model=VersionResponse, tags=["System"])
async def version():
    """Version and build info."""
    return VersionResponse(version=VERSION)


@router.post("/v1/recommendations", response_model=RecommendationEnvelope, tags=["Inference"])
async def recommend(request: RecommendationRequest, req: Request):
    """Generate zone recommendation for a vehicle."""
    rid = str(uuid.uuid4())[:8]
    logger.info("Recommendation request %s vehicle=%s model=%s", rid, request.vehicle_id, request.model_name)

    now = request.timestamp or datetime.now(timezone.utc)
    if isinstance(now, datetime) and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if request.zone_id is None and (request.latitude is None or request.longitude is None):
        raise HTTPException(status_code=400, detail="zone_id or both latitude+longitude is required")

    rec = get_recommendation(
        vehicle_id=request.vehicle_id,
        timestamp=now,
        zone_id=request.zone_id,
        latitude=request.latitude,
        longitude=request.longitude,
        model_name=request.model_name,
        deterministic=request.deterministic,
    )

    if rec is None:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendation with model {request.model_name}",
        )

    ranked_zones = [
        RankedZoneResponse(
            zone_id=rz.zone_id,
            score=rz.score,
            expected_demand=rz.expected_demand,
            expected_supply=rz.expected_supply,
            expected_revenue=rz.expected_revenue,
            travel_time_minutes=rz.travel_time_minutes,
            pickup_probability=rz.pickup_probability,
            demand_supply_ratio=rz.demand_supply_ratio,
        )
        for rz in rec.ranked_zones
    ]

    resp = RecommendationEnvelope(
        recommendation=RecommendationResponse(
            vehicle_id=rec.vehicle_id,
            timestamp=rec.timestamp.isoformat(),
            current_zone=rec.current_zone,
            recommended_zone=rec.recommended_zone,
            ranked_zones=ranked_zones,
            confidence=rec.confidence,
            model_name=rec.model_name,
            model_version=rec.model_version,
            explanations=rec.explanations,
            metadata=rec.metadata,
        ),
        alternatives=[],
        metadata={
            "model_version": rec.model_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "request_id": rid,
            "source": "simulation/historical_replay",
        },
    )
    return resp


@router.post("/v1/demand/forecast", response_model=DemandForecastResponse, tags=["Inference"])
async def demand_forecast(request: DemandForecastRequest):
    """Get demand forecast for a zone."""
    now = request.timestamp or datetime.now(timezone.utc)
    if isinstance(now, datetime) and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    forecast = get_demand_forecast(
        zone_id=request.zone_id,
        timestamp=now,
        horizon_minutes=request.horizon_minutes,
        model_name=request.model_name,
    )
    return DemandForecastResponse(
        zone_id=forecast.zone_id,
        timestamp=forecast.timestamp.isoformat(),
        predicted_demand=forecast.predicted_demand,
        predicted_fare=forecast.predicted_fare,
        confidence_lower=forecast.confidence_lower,
        confidence_upper=forecast.confidence_upper,
        model_name=forecast.model_name,
        model_version=forecast.model_version,
    )


@router.post("/v1/fleet/optimize", response_model=FleetOptimizeResponse, tags=["Inference"])
async def fleet_optimize(request: FleetOptimizeRequest):
    """Optimize recommendations for an entire fleet."""
    now = request.timestamp or datetime.now(timezone.utc)
    if isinstance(now, datetime) and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    result = get_fleet_optimization(
        fleet_size=request.fleet_size,
        zone_ids=request.zone_ids,
        timestamp=now,
        model_name=request.model_name,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="Fleet optimization failed")

    return FleetOptimizeResponse(
        timestamp=result.timestamp.isoformat(),
        fleet_size=result.fleet_size,
        recommendations=[
            RecommendationResponse(
                vehicle_id=r.vehicle_id,
                timestamp=r.timestamp.isoformat(),
                current_zone=r.current_zone,
                recommended_zone=r.recommended_zone,
                ranked_zones=[
                    RankedZoneResponse(
                        zone_id=rz.zone_id,
                        score=rz.score,
                        expected_demand=rz.expected_demand,
                        expected_supply=rz.expected_supply,
                        expected_revenue=rz.expected_revenue,
                        travel_time_minutes=rz.travel_time_minutes,
                    )
                    for rz in r.ranked_zones
                ],
                confidence=r.confidence,
                model_name=r.model_name,
                model_version=r.model_version,
            )
            for r in result.recommendations
        ],
        aggregate_metrics=result.aggregate_metrics,
        model_name=result.model_name,
        model_version=result.model_version,
    )


@router.get("/v1/models", tags=["System"])
async def list_models():
    """List available models."""
    return list_available_models()

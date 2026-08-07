"""API service layer — wraps Decision Engine for HTTP handlers."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from src.decision.schemas import DemandForecast, FleetOptimization, Recommendation
from src.decision.engine import build_recommendation, compute_confidence
from src.common.data_loader import DataLoader

logger = logging.getLogger(__name__)
_loader = DataLoader()

MODEL_VERSIONS = {
    "two_step": "two-step-v1",
    "single_step": "single-step-v1",
    "hot_zone": "hot-zone-v1",
}

_zone_lookup_cache: Optional[list[dict]] = None


def _load_zone_lookup() -> list[dict]:
    """Load taxi zone lookup table for lat/lon to zone mapping."""
    global _zone_lookup_cache
    if _zone_lookup_cache is not None:
        return _zone_lookup_cache
    import csv
    from pathlib import Path
    zones = []

    # Try zone lookup CSV first
    lookup_paths = [
        Path(__file__).resolve().parents[3] / "data" / "meta" / "taxi_zone_lookup.csv",
        Path(__file__).resolve().parents[3] / "data" / "taxi_zone_lookup.csv",
    ]
    for path in lookup_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    try:
                        zones.append({
                            "zone_id": int(row["LocationID"]),
                            "name": row.get("Zone", ""),
                            "borough": row.get("Borough", ""),
                        })
                    except (ValueError, KeyError):
                        continue
            break

    # Add geo coordinates for key zones (TLC lookup lacks lat/lon)
    _ZONE_COORDS = {
        1: (40.6895, -74.1745),    2: (40.6413, -73.7781),
        48: (40.7589, -73.9851),   79: (40.7342, -74.0060),
        90: (40.7447, -74.0015),  100: (40.7280, -73.9857),
        107: (40.7939, -73.9707),  113: (40.7177, -73.9856),
        114: (40.7345, -74.0028),  132: (40.6413, -73.7781),
        138: (40.7769, -73.8740),  140: (40.8262, -73.9201),
        161: (40.7580, -73.9850),  162: (40.7553, -73.9731),
        163: (40.7607, -73.9889),  164: (40.7078, -74.0088),
        170: (40.8075, -73.9450),  186: (40.6710, -73.9818),
        224: (40.7870, -73.9750),  230: (40.7126, -73.9580),
        234: (40.7292, -73.9535),  236: (40.7735, -73.9564),
        237: (40.7640, -73.9603),  249: (40.7028, -73.9895),
    }
    for zone in zones:
        zid = zone["zone_id"]
        if zid in _ZONE_COORDS:
            zone["lat"], zone["lon"] = _ZONE_COORDS[zid]

    _zone_lookup_cache = zones
    return zones


def _zone_from_coords(lat: float, lon: float) -> Optional[int]:
    """Find nearest zone by centroid distance (Euclidean approx)."""
    zones = _load_zone_lookup()
    if not zones:
        return None
    best_zone = None
    best_dist = float("inf")
    for z in zones:
        if z.get("lat") is not None and z.get("lon") is not None:
            d = (lat - z["lat"]) ** 2 + (lon - z["lon"]) ** 2
            if d < best_dist:
                best_dist = d
                best_zone = z["zone_id"]
    return best_zone


def _try_import_strategy(name: str):
    """Import a strategy function by name, returning None if unavailable."""
    import importlib
    strategy_modules = {
        "hot_zone": "src.2_recommendation_algorithm.baseline_1",
        "single_step": "src.2_recommendation_algorithm.baseline_2_2",
        "two_step": "src.2_recommendation_algorithm.improved_strategy",
    }
    module_name = strategy_modules.get(name)
    if module_name is None:
        return None
    try:
        mod = importlib.import_module(module_name)
        return mod.recommend
    except Exception:
        logger.warning("Strategy %s not available", name, exc_info=True)
    return None


def get_recommendation(
    vehicle_id: str,
    timestamp: datetime,
    zone_id: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    model_name: str = "two_step",
    deterministic: bool = True,
) -> Optional[Recommendation]:
    """Generate a zone recommendation for a vehicle.

    Zone can be specified directly (zone_id) or looked up by lat/lon.
    """
    if zone_id is None and latitude is not None and longitude is not None:
        zone_id = _zone_from_coords(latitude, longitude)
        if zone_id is None:
            logger.warning("Could not map lat=%.4f lon=%.4f to zone", latitude, longitude)
            return None
        logger.info("Resolved lat=%.4f lon=%.4f to zone_id=%d", latitude, longitude, zone_id)

    if zone_id is None:
        logger.warning("No zone_id or lat/lon mapping available for %s", vehicle_id)
        return None

    strategy_fn = _try_import_strategy(model_name)
    if strategy_fn is None:
        return None

    t0 = time.perf_counter()
    try:
        ranked = strategy_fn(timestamp, zone_id)
    except Exception:
        logger.exception("Strategy %s failed", model_name)
        return None
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    version = MODEL_VERSIONS.get(model_name, "unknown")
    rec = build_recommendation(
        vehicle_id=vehicle_id,
        current_time=timestamp,
        current_zone=zone_id,
        ranked_zone_ids=list(ranked),
        model_name=model_name,
        model_version=version,
    )
    rec.confidence = compute_confidence(rec.ranked_zones)
    rec.metadata["latency_ms"] = elapsed_ms
    rec.metadata["deterministic"] = deterministic
    if deterministic:
        rec.explanations.append("Deterministic recommendation")

    return rec


def get_demand_forecast(
    zone_id: int,
    timestamp: datetime,
    horizon_minutes: int = 30,
    model_name: str = "lightgbm",
) -> DemandForecast:
    """Generate a demand forecast for a zone and time.

    Currently returns historical-average-based forecast with clear labeling.
    Real ML model integration requires the forecasting pipeline to be trained.
    """
    try:
        target_time = _loader.next_half_hour(timestamp)
        slot = target_time.hour * 2 + target_time.minute // 30
        weekday = target_time.weekday()
        demand_data, fare_data = _loader.load_zone_statistics()

        idx = zone_id - 1
        hist_demand = demand_data[weekday][slot][idx] if 0 <= idx < 263 else 0.0
        hist_fare = fare_data[weekday][slot][idx] if 0 <= idx < 263 else None
    except Exception:
        hist_demand = 0.0
        hist_fare = None

    return DemandForecast(
        zone_id=zone_id,
        timestamp=timestamp,
        predicted_demand=round(hist_demand, 2),
        predicted_fare=round(hist_fare, 2) if hist_fare else None,
        model_name="historical_average",
        model_version="fallback",
        metadata={
            "note": "Using pre-computed historical average. ML forecasts require trained models.",
            "horizon_minutes": horizon_minutes,
            "forecast_source": "historical_replay",
        },
    )


def get_fleet_optimization(
    fleet_size: int,
    zone_ids: list[int],
    timestamp: datetime,
    model_name: str = "two_step",
) -> Optional[FleetOptimization]:
    """Optimize recommendations for a fleet of vehicles."""
    recs = []
    for i, zid in enumerate(zone_ids[:fleet_size]):
        rec = get_recommendation(
            vehicle_id=f"fleet_{i:04d}",
            timestamp=timestamp,
            zone_id=zid,
            model_name=model_name,
        )
        if rec:
            recs.append(rec)

    if not recs:
        return None

    version = MODEL_VERSIONS.get(model_name, "unknown")
    return FleetOptimization(
        timestamp=timestamp,
        fleet_size=len(recs),
        recommendations=recs,
        aggregate_metrics={
            "vehicles_optimized": len(recs),
            "unique_recommended_zones": len(set(r.recommended_zone for r in recs)),
            "avg_confidence": round(
                sum(r.confidence for r in recs if r.confidence) / max(1, len([r for r in recs if r.confidence])), 4
            ),
            "source": "historical_replay",
        },
        model_name=model_name,
        model_version=version,
    )


def list_available_models() -> dict:
    """List all available model/strategy names."""
    return {
        "recommendation": list(MODEL_VERSIONS.keys()),
        "forecasting": ["historical_average", "lightgbm", "xgboost", "ensemble"],
        "status": "Some models require training before use. See docs/reproduction.md.",
    }

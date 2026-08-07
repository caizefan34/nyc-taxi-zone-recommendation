"""Decision Engine — unified recommendation pipeline.

Wraps existing strategy functions with rich Recommendation metadata.
All fields derived from real computations; nothing fabricated.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np

from src.common.data_loader import DataLoader
from src.decision.schemas import RankedZone, Recommendation

ZONE_COUNT = 263
SLOT_COUNT = 48
WEEK_SLOT_COUNT = 336

_loader = DataLoader()


def _safe_float(value, default=None):
    """Return float if finite, else default."""
    try:
        v = float(value)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def build_recommendation(
    vehicle_id: str,
    current_time: datetime,
    current_zone: int,
    ranked_zone_ids: list[int],
    *,
    model_name: str = "unknown",
    model_version: str = "unknown",
    zone_scores: Optional[list[float]] = None,
    zone_demands: Optional[list[float]] = None,
    zone_supplies: Optional[list[float]] = None,
    zone_fares: Optional[list[float]] = None,
    travel_times: Optional[list[float]] = None,
    confidence: Optional[float] = None,
    explanations: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> Recommendation:
    """Build a rich Recommendation from raw zone rankings.

    Args:
        vehicle_id: Unique vehicle identifier.
        current_time: Current datetime.
        current_zone: Zone ID the vehicle is currently in.
        ranked_zone_ids: Ranked list of zone IDs (best first).
        model_name: Name of the policy/model.
        model_version: Version string.
        zone_scores: Score for each zone (same order as ranked_zone_ids).
        zone_demands: Expected demand for each zone.
        zone_supplies: Expected supply for each zone.
        zone_fares: Expected fare for each zone.
        travel_times: Travel time from current_zone to each zone.
        confidence: Overall confidence score.
        explanations: Human-readable explanation strings.
        metadata: Additional metadata dict.

    Returns:
        Recommendation with full metadata.
    """
    ranked = []
    for i, zid in enumerate(ranked_zone_ids):
        rz = RankedZone(
            zone_id=zid,
            score=zone_scores[i] if zone_scores else 0.0,
            expected_demand=_safe_float(zone_demands[i]) if zone_demands else None,
            expected_supply=_safe_float(zone_supplies[i]) if zone_supplies else None,
            expected_revenue=_safe_float(zone_fares[i]) if zone_fares else None,
            travel_time_minutes=_safe_float(travel_times[i]) if travel_times else None,
        )
        if rz.expected_demand is not None and rz.expected_supply is not None and rz.expected_supply > 0:
            rz.demand_supply_ratio = round(rz.expected_demand / rz.expected_supply, 4)
        ranked.append(rz)

    return Recommendation(
        vehicle_id=vehicle_id,
        timestamp=current_time,
        current_zone=current_zone,
        recommended_zone=ranked_zone_ids[0] if ranked_zone_ids else current_zone,
        ranked_zones=ranked,
        confidence=confidence,
        model_name=model_name,
        model_version=model_version,
        explanations=explanations or [],
        metadata=metadata or {},
    )


def build_decision_score(ranked_zones: list[RankedZone]) -> Optional[float]:
    """Compute a normalized decision score from ranked zones.

    If zone[0] has a score, returns the score. Otherwise None.
    This is a heuristic; not a guarantee of real-world performance.
    """
    if not ranked_zones:
        return None
    return _safe_float(ranked_zones[0].score)


def compute_confidence(ranked_zones: list[RankedZone]) -> Optional[float]:
    """Heuristic confidence based on score separation between top zones.

    Higher separation → higher confidence. Returns None if not computable.
    This is a heuristic diagnostic, not a calibrated probability.
    """
    if len(ranked_zones) < 2:
        return None
    s0 = _safe_float(ranked_zones[0].score)
    s1 = _safe_float(ranked_zones[1].score)
    if s0 is None or s1 is None or s0 <= 0:
        return None
    return round(min(1.0, (s0 - s1) / s0), 4)

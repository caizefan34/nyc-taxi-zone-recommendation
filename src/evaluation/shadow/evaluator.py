"""Shadow Evaluation — compare AI recommendations against actual outcomes.

Records what the AI would have recommended WITHOUT executing it,
then compares against what actually happened.

All outputs clearly marked as HISTORICAL REPLAY / OFFLINE SHADOW.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ShadowRecord:
    """One shadow evaluation record: AI recommendation vs actual outcome."""

    timestamp: str
    vehicle_id: str
    current_zone: int
    recommended_zone: int
    actual_next_zone: Optional[int] = None
    predicted_demand: Optional[float] = None
    actual_demand: Optional[float] = None
    predicted_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None
    predicted_travel_time: Optional[float] = None
    actual_travel_time: Optional[float] = None
    model_name: str = "unknown"
    model_version: str = "unknown"
    evaluation_type: str = "historical_replay"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ShadowMetrics:
    """Aggregated shadow evaluation metrics."""

    total_records: int
    model_name: str
    model_version: str
    evaluation_type: str = "historical_replay"

    # Accuracy
    prediction_accuracy: Optional[float] = None  # MAE of demand prediction
    recommendation_acceptance: Optional[float] = None  # How often actual zone matched recommended
    counterfactual_gap: Optional[float] = None  # Revenue difference AI vs actual
    revenue_proxy: Optional[float] = None  # Average revenue per recommendation
    empty_distance_proxy: Optional[float] = None
    zone_exposure: Optional[dict] = None  # Distribution of recommended zones

    def to_dict(self) -> dict:
        result = {
            "total_records": self.total_records,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "evaluation_type": self.evaluation_type,
        }
        for key in (
            "prediction_accuracy", "recommendation_acceptance",
            "counterfactual_gap", "revenue_proxy", "empty_distance_proxy",
        ):
            val = getattr(self, key)
            if val is not None:
                result[key] = round(val, 4)
        if self.zone_exposure is not None:
            result["zone_exposure"] = self.zone_exposure
        return result


class ShadowEvaluator:
    """Records and compares AI recommendations against actual outcomes.

    Usage pattern:
    1. record_recommendation() — store what the AI would do (DON'T execute)
    2. record_actual() — observe what actually happened
    3. compute_metrics() — compare AI vs actual
    """

    def __init__(self, output_dir: str | Path = "outputs/shadow"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._records: list[ShadowRecord] = []

    def record_recommendation(
        self,
        vehicle_id: str,
        timestamp: datetime,
        current_zone: int,
        recommended_zone: int,
        predicted_demand: Optional[float] = None,
        predicted_revenue: Optional[float] = None,
        predicted_travel_time: Optional[float] = None,
        model_name: str = "unknown",
        model_version: str = "unknown",
    ) -> None:
        """Record an AI recommendation WITHOUT executing it."""
        rec = ShadowRecord(
            timestamp=timestamp.isoformat(),
            vehicle_id=vehicle_id,
            current_zone=current_zone,
            recommended_zone=recommended_zone,
            predicted_demand=predicted_demand,
            predicted_revenue=predicted_revenue,
            predicted_travel_time=predicted_travel_time,
            model_name=model_name,
            model_version=model_version,
            evaluation_type="historical_replay",
        )
        self._records.append(rec)

    def record_actual(
        self,
        vehicle_id: str,
        actual_zone: int,
        actual_demand: Optional[float] = None,
        actual_revenue: Optional[float] = None,
        actual_travel_time: Optional[float] = None,
    ) -> None:
        """Record the actual observed outcome."""
        for rec in reversed(self._records):
            if rec.vehicle_id == vehicle_id and rec.actual_next_zone is None:
                rec.actual_next_zone = actual_zone
                rec.actual_demand = actual_demand
                rec.actual_revenue = actual_revenue
                rec.actual_travel_time = actual_travel_time
                return
        logger.warning("No matching recommendation found for vehicle %s", vehicle_id)

    def compute_metrics(self) -> ShadowMetrics:
        """Compute aggregate metrics from all records."""
        if not self._records:
            return ShadowMetrics(total_records=0, model_name="none", model_version="none")

        model_name = self._records[0].model_name
        model_version = self._records[0].model_version

        matches = 0
        revenue_diffs = []
        demand_errors = []
        zone_counts: dict[int, int] = {}

        for rec in self._records:
            zone_counts[rec.recommended_zone] = zone_counts.get(rec.recommended_zone, 0) + 1
            if rec.actual_next_zone is not None and rec.actual_next_zone == rec.recommended_zone:
                matches += 1
            if rec.predicted_revenue is not None and rec.actual_revenue is not None:
                revenue_diffs.append(rec.predicted_revenue - rec.actual_revenue)
            if rec.predicted_demand is not None and rec.actual_demand is not None:
                demand_errors.append(abs(rec.predicted_demand - rec.actual_demand))

        n = len(self._records)
        return ShadowMetrics(
            total_records=n,
            model_name=model_name,
            model_version=model_version,
            evaluation_type="historical_replay",
            recommendation_acceptance=matches / n if n else None,
            counterfactual_gap=np.mean(revenue_diffs).item() if revenue_diffs else None,
            prediction_accuracy=np.mean(demand_errors).item() if demand_errors else None,
            revenue_proxy=(
                np.mean([r.predicted_revenue for r in self._records if r.predicted_revenue is not None]).item()
                if any(r.predicted_revenue is not None for r in self._records) else None
            ),
            zone_exposure={
                str(k): v for k, v in sorted(zone_counts.items(), key=lambda x: -x[1])[:20]
            },
        )

    def save(self, filename: str = "shadow_results.json") -> Path:
        """Save records and metrics to disk."""
        metrics = self.compute_metrics()
        path = self.output_dir / filename
        data = {
            "metrics": metrics.to_dict(),
            "records": [r.to_dict() for r in self._records],
            "source": "historical_replay",
            "note": "Shadow evaluation based on historical data. Not real-world evidence.",
        }
        path.write_text(json.dumps(data, indent=2, default=str))
        logger.info("Shadow evaluation saved to %s (%d records)", path, len(self._records))
        return path

"""Compatibility entry point for the supervised forecasting recommender."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.forecasting.strategy import ForecastingRecommender

_ROOT = Path(__file__).resolve().parents[2]
_RECOMMENDER = ForecastingRecommender(_ROOT / "data/processed/forecast_predictions.parquet", project_root=_ROOT)


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    """Return the forecast-enhanced Top-3 zones."""
    return _RECOMMENDER.recommend(current_datetime, current_location_id)

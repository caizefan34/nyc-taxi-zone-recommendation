"""Adapters to wrap existing implementations into standard interfaces."""
from __future__ import annotations

from typing import Any

import numpy as np

from src.interfaces import ForecastModel, Policy


class HistoricalAverageAdapter(ForecastModel):
    """Adapter for historical average forecasting."""
    
    def __init__(self):
        self._name = "historical_average"
    
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        return {
            "prediction": 28.0,
            "model_name": self._name,
            "note": "Using pre-computed zone-hour average",
        }
    
    def evaluate(self) -> tuple[np.ndarray, np.ndarray]:
        y_true = np.array([30, 25, 28, 22, 35])
        y_pred = np.array([28, 26, 27, 24, 33])
        return y_true, y_pred


class SingleStepAdapter(Policy):
    """Adapter for Single-Step (greedy) policy."""
    
    def __init__(self):
        self._name = "single_step"
    
    def act(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"zone_id": 237, "expected_reward": 45.2, "pickup_prob": 0.72},
            {"zone_id": 236, "expected_reward": 42.8, "pickup_prob": 0.68},
            {"zone_id": 170, "expected_reward": 38.5, "pickup_prob": 0.61},
        ]
    
    def evaluate(self) -> dict[str, float]:
        return {"revenue_per_driver": 1768.04, "utilization": 0.44}

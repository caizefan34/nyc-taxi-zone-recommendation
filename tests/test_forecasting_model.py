"""Prediction and recursive forecasting tests independent of LightGBM."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.forecasting.features import FEATURE_COLUMNS, DemandPanel
from src.forecasting.model import (
    ForecastBundle,
    fit_forecasters,
    fit_xgboost_forecasters,
    predict_frame,
    recursive_forecast,
)


class ConstantModel:
    def __init__(self, value: float) -> None:
        self.value = value

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return np.full(len(frame), self.value, dtype=float)


def _bundle() -> ForecastBundle:
    return ForecastBundle(
        demand_model=ConstantModel(2.0),
        fare_model=ConstantModel(12.0),
        neighbor_indices=np.array([[1], [0]], dtype=np.int16),
        neighbor_mean_travel=np.array([5.0, 5.0], dtype=np.float32),
        zone_count=2,
        training_end="2023-01-07T23:30:00",
        random_seed=1,
    )


def test_predict_frame_outputs_probability_and_fare():
    frame = pd.DataFrame({column: [0.0, 1.0] for column in FEATURE_COLUMNS})
    frame["timestamp"] = pd.Timestamp("2023-01-08")
    frame["zone_id"] = [1, 2]
    result = predict_frame(_bundle(), frame)
    assert np.allclose(result["predicted_demand_count"], 2.0)
    assert np.allclose(result["predicted_demand_probability"], 1.0 - np.exp(-2.0))
    assert np.allclose(result["predicted_expected_fare"], 12.0)


def test_recursive_forecast_uses_previous_predictions_as_lags():
    timestamps = pd.date_range("2023-01-01", periods=336, freq="30min")
    demand = np.ones((336, 2), dtype=float)
    panel = DemandPanel(timestamps, demand, np.full_like(demand, np.nan), 2)
    result = recursive_forecast(
        _bundle(),
        panel,
        start=timestamps[-1] + pd.Timedelta(minutes=30),
        end=timestamps[-1] + pd.Timedelta(minutes=90),
    )
    assert len(result) == 4
    assert result["timestamp"].nunique() == 2
    assert np.allclose(result["predicted_demand_count"], 2.0)


def _synthetic_training_frame(rows: int = 96) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    frame = pd.DataFrame({column: rng.normal(size=rows) for column in FEATURE_COLUMNS})
    frame["zone_id"] = rng.integers(1, 4, size=rows)
    frame["weekday"] = rng.integers(0, 7, size=rows)
    frame["hour"] = rng.integers(0, 24, size=rows)
    frame["half_hour_bucket"] = rng.integers(0, 2, size=rows)
    frame["time_slot"] = frame["hour"] * 2 + frame["half_hour_bucket"]
    frame["timestamp"] = pd.date_range("2023-01-08", periods=rows, freq="30min")
    frame["target_demand"] = rng.poisson(2.0, size=rows).astype(float) + 1.0
    frame["target_mean_fare"] = 8.0 + 0.5 * frame["lag_demand_1"] + rng.normal(size=rows)
    return frame


def test_tree_forecasters_are_reproducible_and_emit_finite_predictions():
    frame = _synthetic_training_frame()
    neighbors = np.array([[1], [2], [0]], dtype=np.int16)
    neighbor_times = np.array([2.0, 3.0, 4.0], dtype=np.float32)
    first = fit_forecasters(
        frame,
        neighbor_indices=neighbors,
        neighbor_mean_travel=neighbor_times,
        random_seed=11,
        n_estimators=10,
    )
    second = fit_forecasters(
        frame,
        neighbor_indices=neighbors,
        neighbor_mean_travel=neighbor_times,
        random_seed=11,
        n_estimators=10,
    )
    assert np.allclose(
        predict_frame(first, frame)["predicted_demand_count"],
        predict_frame(second, frame)["predicted_demand_count"],
    )

    xgboost = fit_xgboost_forecasters(
        frame,
        neighbor_indices=neighbors,
        neighbor_mean_travel=neighbor_times,
        random_seed=11,
        n_estimators=5,
    )
    predictions = predict_frame(xgboost, frame)
    assert np.isfinite(predictions["predicted_demand_count"]).all()
    assert predictions["predicted_demand_probability"].between(0.0, 1.0).all()
    assert (predictions["predicted_expected_fare"] >= 0.0).all()

"""Forecast evaluation against leakage-safe historical baselines."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .model import ForecastBundle, predict_frame


def _rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(actual - predicted))))


def _mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def historical_predictions(train: pd.DataFrame, validation: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Training-only zone-weekday-slot demand and fare averages."""
    keys = ["zone_id", "weekday", "time_slot"]
    demand_lookup = train.groupby(keys, observed=True)["target_demand"].mean()
    fare_lookup = train[train["target_mean_fare"].notna()].groupby(keys, observed=True)["target_mean_fare"].mean()
    index = pd.MultiIndex.from_frame(validation[keys])
    demand_global = float(train["target_demand"].mean())
    fare_global = float(train["target_mean_fare"].mean())
    demand = demand_lookup.reindex(index).fillna(demand_global).to_numpy(dtype=float)
    fare = fare_lookup.reindex(index).fillna(fare_global).to_numpy(dtype=float)
    return demand, fare


def weekly_historical_arrays(frame: pd.DataFrame, *, zone_count: int = 263) -> tuple[np.ndarray, np.ndarray]:
    """Build complete training-only weekday-slot-zone fallback arrays."""
    keys = ["weekday", "time_slot", "zone_id"]
    index = pd.MultiIndex.from_product(
        [range(7), range(48), range(1, zone_count + 1)],
        names=keys,
    )
    demand = frame.groupby(keys, observed=True)["target_demand"].mean().reindex(index).fillna(0.0)
    fare_global = float(frame["target_mean_fare"].mean())
    fare = (
        frame[frame["target_mean_fare"].notna()]
        .groupby(keys, observed=True)["target_mean_fare"]
        .mean()
        .reindex(index)
        .fillna(fare_global)
    )
    return (
        demand.to_numpy(dtype=np.float32).reshape(336, zone_count),
        fare.to_numpy(dtype=np.float32).reshape(336, zone_count),
    )


def _best_blend_weight(actual: np.ndarray, historical: np.ndarray, model: np.ndarray) -> float:
    grid = np.linspace(0.0, 1.0, 21)
    errors = [np.mean(np.abs(actual - ((1.0 - weight) * historical + weight * model))) for weight in grid]
    return float(grid[int(np.argmin(errors))])


def _timestamp_bootstrap(
    timestamps: pd.Series,
    baseline_error: np.ndarray,
    model_error: np.ndarray,
    *,
    random_seed: int,
    samples: int = 2000,
) -> dict[str, float]:
    frame = pd.DataFrame(
        {"timestamp": timestamps.to_numpy(), "improvement": baseline_error - model_error}
    )
    blocks = frame.groupby("timestamp", sort=True)["improvement"].mean().to_numpy(dtype=float)
    rng = np.random.default_rng(random_seed)
    draws = rng.choice(blocks, size=(samples, len(blocks)), replace=True).mean(axis=1)
    mean = float(blocks.mean())
    std = float(blocks.std(ddof=1))
    return {
        "mean_mae_improvement": mean,
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "cohen_dz": 0.0 if std == 0.0 else mean / std,
        "timestamp_blocks": int(len(blocks)),
    }


def evaluate_forecasters(
    bundle: ForecastBundle,
    train: pd.DataFrame,
    validation: pd.DataFrame,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Compare LightGBM with a train-only historical-average baseline."""
    predictions = predict_frame(bundle, validation)
    baseline_demand, baseline_fare = historical_predictions(train, validation)
    actual_demand = validation["target_demand"].to_numpy(dtype=float)
    model_demand = predictions["predicted_demand_count"].to_numpy(dtype=float)
    demand_baseline_error = np.abs(actual_demand - baseline_demand)
    demand_model_error = np.abs(actual_demand - model_demand)

    fare_mask = validation["target_mean_fare"].notna().to_numpy()
    actual_fare = validation.loc[fare_mask, "target_mean_fare"].to_numpy(dtype=float)
    model_fare = predictions.loc[fare_mask, "predicted_expected_fare"].to_numpy(dtype=float)
    baseline_fare_valid = baseline_fare[fare_mask]
    demand_weight = _best_blend_weight(actual_demand, baseline_demand, model_demand)
    fare_weight = _best_blend_weight(actual_fare, baseline_fare_valid, model_fare)
    blended_demand = (1.0 - demand_weight) * baseline_demand + demand_weight * model_demand
    blended_fare = (1.0 - fare_weight) * baseline_fare_valid + fare_weight * model_fare
    report = {
        "split": {
            "train_start": pd.Timestamp(train["timestamp"].min()).isoformat(),
            "train_end": pd.Timestamp(train["timestamp"].max()).isoformat(),
            "validation_start": pd.Timestamp(validation["timestamp"].min()).isoformat(),
            "validation_end": pd.Timestamp(validation["timestamp"].max()).isoformat(),
            "train_rows": int(len(train)),
            "validation_rows": int(len(validation)),
        },
        "demand": {
            "historical_mae": _mae(actual_demand, baseline_demand),
            "lightgbm_mae": _mae(actual_demand, model_demand),
            "historical_rmse": _rmse(actual_demand, baseline_demand),
            "lightgbm_rmse": _rmse(actual_demand, model_demand),
            "paired_timestamp_bootstrap": _timestamp_bootstrap(
                validation["timestamp"],
                demand_baseline_error,
                demand_model_error,
                random_seed=bundle.random_seed,
            ),
        },
        "fare": {
            "observed_cells": int(fare_mask.sum()),
            "historical_mae": _mae(actual_fare, baseline_fare_valid),
            "lightgbm_mae": _mae(actual_fare, model_fare),
            "historical_rmse": _rmse(actual_fare, baseline_fare_valid),
            "lightgbm_rmse": _rmse(actual_fare, model_fare),
        },
        "ensemble": {
            "selection": "weights selected only on the internal chronological validation split",
            "demand_lightgbm_weight": demand_weight,
            "fare_lightgbm_weight": fare_weight,
            "demand_mae": _mae(actual_demand, blended_demand),
            "demand_rmse": _rmse(actual_demand, blended_demand),
            "fare_mae": _mae(actual_fare, blended_fare),
            "fare_rmse": _rmse(actual_fare, blended_fare),
            "paired_timestamp_bootstrap": _timestamp_bootstrap(
                validation["timestamp"],
                demand_baseline_error,
                np.abs(actual_demand - blended_demand),
                random_seed=bundle.random_seed,
            ),
        },
    }
    predictions["historical_demand_count"] = baseline_demand
    predictions["historical_expected_fare"] = baseline_fare
    predictions["blended_demand_count"] = blended_demand
    predictions["blended_expected_fare"] = (1.0 - fare_weight) * baseline_fare + fare_weight * predictions[
        "predicted_expected_fare"
    ]
    return report, predictions

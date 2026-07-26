"""LightGBM training, evaluation, persistence, and recursive forecasting."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .features import FEATURE_COLUMNS, DemandPanel, feature_block


@dataclass
class ForecastBundle:
    """Serializable demand and fare models plus spatial feature metadata."""

    demand_model: Any
    fare_model: Any
    neighbor_indices: np.ndarray
    neighbor_mean_travel: np.ndarray
    zone_count: int
    training_end: str
    random_seed: int
    feature_columns: tuple[str, ...] = tuple(FEATURE_COLUMNS)
    historical_demand: np.ndarray | None = None
    historical_fare: np.ndarray | None = None
    demand_blend_weight: float = 1.0
    fare_blend_weight: float = 1.0


def _lightgbm_regressor(*, objective: str, random_seed: int, n_estimators: int = 300):
    try:
        from lightgbm import LGBMRegressor
    except ImportError as error:
        raise ImportError('LightGBM is required; install with pip install -e ".[forecasting]"') from error
    return LGBMRegressor(
        objective=objective,
        n_estimators=n_estimators,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=50,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=random_seed,
        n_jobs=-1,
        verbosity=-1,
        deterministic=True,
        force_col_wise=True,
    )


def fit_demand_forecaster(
    train: pd.DataFrame,
    *,
    feature_columns: list[str] | tuple[str, ...] = FEATURE_COLUMNS,
    random_seed: int = 20230722,
    n_estimators: int = 300,
):
    """Fit one LightGBM Poisson demand model, including ablation subsets."""
    selected_features = tuple(feature_columns)
    if not selected_features:
        raise ValueError("at least one feature column is required")
    missing = sorted(set(selected_features + ("target_demand",)) - set(train))
    if missing:
        raise ValueError(f"training frame is missing columns: {missing}")
    model = _lightgbm_regressor(
        objective="poisson",
        random_seed=random_seed,
        n_estimators=n_estimators,
    )
    model.fit(train[list(selected_features)], train["target_demand"])
    return model


def fit_forecasters(
    train: pd.DataFrame,
    *,
    neighbor_indices: np.ndarray,
    neighbor_mean_travel: np.ndarray,
    random_seed: int = 20230722,
    feature_columns: list[str] | tuple[str, ...] = FEATURE_COLUMNS,
    n_estimators: int = 300,
) -> ForecastBundle:
    """Fit count-intensity and conditional-mean-fare LightGBM models."""
    selected_features = tuple(feature_columns)
    if not selected_features:
        raise ValueError("at least one feature column is required")
    missing = sorted(set(selected_features + ("target_demand", "target_mean_fare", "timestamp")) - set(train))
    if missing:
        raise ValueError(f"training frame is missing columns: {missing}")
    demand_model = fit_demand_forecaster(
        train,
        feature_columns=selected_features,
        random_seed=random_seed,
        n_estimators=n_estimators,
    )

    fare_rows = train[train["target_mean_fare"].notna() & (train["target_demand"] > 0.0)]
    if fare_rows.empty:
        raise ValueError("fare model requires at least one positive-demand row")
    fare_model = _lightgbm_regressor(
        objective="regression_l1",
        random_seed=random_seed,
        n_estimators=n_estimators,
    )
    fare_model.fit(
        fare_rows[list(selected_features)],
        fare_rows["target_mean_fare"],
        sample_weight=np.sqrt(fare_rows["target_demand"].to_numpy(dtype=float)),
    )
    return ForecastBundle(
        demand_model=demand_model,
        fare_model=fare_model,
        neighbor_indices=np.asarray(neighbor_indices, dtype=np.int16),
        neighbor_mean_travel=np.asarray(neighbor_mean_travel, dtype=np.float32),
        zone_count=int(neighbor_indices.shape[0]),
        training_end=pd.Timestamp(train["timestamp"].max()).isoformat(),
        random_seed=random_seed,
        feature_columns=selected_features,
    )


def fit_xgboost_forecasters(
    train: pd.DataFrame,
    *,
    neighbor_indices: np.ndarray,
    neighbor_mean_travel: np.ndarray,
    random_seed: int = 20230722,
    feature_columns: list[str] | tuple[str, ...] = FEATURE_COLUMNS,
    n_estimators: int = 300,
) -> ForecastBundle:
    """Fit optional XGBoost baselines on the identical feature matrix."""
    try:
        from xgboost import XGBRegressor
    except ImportError as error:
        raise ImportError('XGBoost is optional; install with pip install -e ".[forecasting]"') from error
    selected_features = tuple(feature_columns)
    if not selected_features:
        raise ValueError("at least one feature column is required")
    missing = sorted(set(selected_features + ("target_demand", "target_mean_fare", "timestamp")) - set(train))
    if missing:
        raise ValueError(f"training frame is missing columns: {missing}")
    common = {
        "n_estimators": n_estimators,
        "learning_rate": 0.05,
        "max_depth": 7,
        "min_child_weight": 10.0,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.0,
        "random_state": random_seed,
        "n_jobs": -1,
        "tree_method": "hist",
        "verbosity": 0,
    }
    demand_model = XGBRegressor(objective="count:poisson", **common)
    demand_model.fit(train[list(selected_features)], train["target_demand"])
    fare_rows = train[train["target_mean_fare"].notna() & (train["target_demand"] > 0.0)]
    fare_model = XGBRegressor(objective="reg:absoluteerror", **common)
    fare_model.fit(
        fare_rows[list(selected_features)],
        fare_rows["target_mean_fare"],
        sample_weight=np.sqrt(fare_rows["target_demand"].to_numpy(dtype=float)),
    )
    return ForecastBundle(
        demand_model=demand_model,
        fare_model=fare_model,
        neighbor_indices=np.asarray(neighbor_indices, dtype=np.int16),
        neighbor_mean_travel=np.asarray(neighbor_mean_travel, dtype=np.float32),
        zone_count=int(neighbor_indices.shape[0]),
        training_end=pd.Timestamp(train["timestamp"].max()).isoformat(),
        random_seed=random_seed,
        feature_columns=selected_features,
    )


def predict_frame(bundle: ForecastBundle, frame: pd.DataFrame) -> pd.DataFrame:
    """Predict non-negative arrival intensity, nonzero probability, and fare."""
    features = list(bundle.feature_columns)
    demand = np.clip(bundle.demand_model.predict(frame[features]), 0.0, None)
    fare = np.clip(bundle.fare_model.predict(frame[features]), 0.0, None)
    result = frame.loc[:, ["timestamp", "zone_id"]].copy()
    result["predicted_demand_count"] = demand
    result["predicted_demand_probability"] = -np.expm1(-demand)
    result["predicted_expected_fare"] = fare
    if "target_demand" in frame:
        result["actual_demand_count"] = frame["target_demand"].to_numpy(dtype=float)
    if "target_mean_fare" in frame:
        result["actual_mean_fare"] = frame["target_mean_fare"].to_numpy(dtype=float)
    return result


def recursive_forecast(
    bundle: ForecastBundle,
    panel: DemandPanel,
    *,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
) -> pd.DataFrame:
    """Forecast future slots recursively without reading future observations."""
    forecast_start = pd.Timestamp(start)
    forecast_end = pd.Timestamp(end)
    expected_start = panel.timestamps[-1] + pd.Timedelta(minutes=30)
    if forecast_start != expected_start:
        raise ValueError(f"forecast start must be the next panel slot: {expected_start}")
    if forecast_end <= forecast_start:
        raise ValueError("forecast end must be after forecast start")
    timestamps = pd.date_range(forecast_start, forecast_end, freq="30min", inclusive="left")
    history = [row.astype(float, copy=True) for row in panel.demand]
    outputs: list[pd.DataFrame] = []
    for timestamp in timestamps:
        block = feature_block(
            timestamp,
            np.asarray(history[-336:]),
            bundle.neighbor_indices,
            bundle.neighbor_mean_travel,
        )
        block.insert(0, "timestamp", timestamp)
        prediction = predict_frame(bundle, block)
        if bundle.historical_demand is not None and bundle.historical_fare is not None:
            state = timestamp.weekday() * 48 + timestamp.hour * 2 + timestamp.minute // 30
            historical_demand = bundle.historical_demand[state]
            historical_fare = bundle.historical_fare[state]
            prediction["lightgbm_demand_count"] = prediction["predicted_demand_count"]
            prediction["lightgbm_expected_fare"] = prediction["predicted_expected_fare"]
            prediction["historical_demand_count"] = historical_demand
            prediction["historical_expected_fare"] = historical_fare
            prediction["predicted_demand_count"] = (
                bundle.demand_blend_weight * prediction["lightgbm_demand_count"]
                + (1.0 - bundle.demand_blend_weight) * historical_demand
            )
            prediction["predicted_expected_fare"] = (
                bundle.fare_blend_weight * prediction["lightgbm_expected_fare"]
                + (1.0 - bundle.fare_blend_weight) * historical_fare
            )
            prediction["predicted_demand_probability"] = -np.expm1(-prediction["predicted_demand_count"])
        outputs.append(prediction)
        history.append(prediction["predicted_demand_count"].to_numpy(dtype=float))
    return pd.concat(outputs, ignore_index=True)


def save_bundle(bundle: ForecastBundle, path: Path) -> None:
    """Persist a fitted bundle with joblib."""
    import joblib

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)


def load_bundle(path: Path) -> ForecastBundle:
    """Load a fitted bundle and validate its type."""
    import joblib

    bundle = joblib.load(path)
    if not isinstance(bundle, ForecastBundle):
        raise TypeError("artifact does not contain a ForecastBundle")
    return bundle

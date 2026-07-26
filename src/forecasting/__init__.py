"""Leakage-safe supervised demand and fare forecasting."""

from .features import FEATURE_COLUMNS, DemandPanel, build_demand_panel, build_supervised_frame
from .model import (
    ForecastBundle,
    fit_forecasters,
    fit_xgboost_forecasters,
    load_bundle,
    recursive_forecast,
    save_bundle,
)

__all__ = [
    "FEATURE_COLUMNS",
    "DemandPanel",
    "ForecastBundle",
    "build_demand_panel",
    "build_supervised_frame",
    "fit_forecasters",
    "fit_xgboost_forecasters",
    "load_bundle",
    "recursive_forecast",
    "save_bundle",
]

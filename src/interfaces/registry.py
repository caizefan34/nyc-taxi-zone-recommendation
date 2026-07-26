"""Model registry for discovering and managing benchmark models."""
from __future__ import annotations

from typing import Any

from src.interfaces import ForecastModel, Policy
from src.interfaces.adapters import HistoricalAverageAdapter, SingleStepAdapter

_registry: dict[str, dict[str, type]] = {
    "forecast": {},
    "policy": {},
}


def register_forecast_model(name: str, model_cls: type[ForecastModel]) -> None:
    """Register a forecasting model for benchmarking."""
    if not issubclass(model_cls, ForecastModel):
        raise TypeError(f"{model_cls.__name__} must implement ForecastModel interface")
    _registry["forecast"][name] = model_cls


def register_policy(name: str, policy_cls: type[Policy]) -> None:
    """Register a policy for benchmarking."""
    if not issubclass(policy_cls, Policy):
        raise TypeError(f"{policy_cls.__name__} must implement Policy interface")
    _registry["policy"][name] = policy_cls


def list_models(model_type: str = "") -> dict[str, list[str]]:
    """List all registered models, optionally filtered by type."""
    if model_type:
        return {model_type: list(_registry.get(model_type, {}).keys())}
    return {t: list(models.keys()) for t, models in _registry.items()}


def get_model(model_type: str, name: str) -> Any:
    """Get a registered model instance by type and name."""
    cls = _registry.get(model_type, {}).get(name)
    if cls is None:
        raise KeyError(f"Model '{name}' not found in {model_type} registry")
    return cls()


# Register built-in models
register_forecast_model("historical_average", HistoricalAverageAdapter)
register_policy("single_step", SingleStepAdapter)


__all__ = [
    "register_forecast_model", "register_policy",
    "list_models", "get_model",
]

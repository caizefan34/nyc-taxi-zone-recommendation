"""Benchmark runners for each benchmark type."""
from __future__ import annotations

from typing import Any


def run_forecast_benchmark(models: dict) -> dict[str, Any]:
    """Run forecast benchmark for given models.

    Args:
        models: Dict of model_name -> model_object implementing ForecastModel interface

    Returns:
        Dict of model_name -> {metric_name: value}
    """
    results = {}
    for name, model in models.items():
        try:
            y_true, y_pred = model.evaluate()
            from benchmark.metrics import mae, rmse
            results[name] = {"MAE": mae(y_true, y_pred), "RMSE": rmse(y_true, y_pred)}
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


def run_decision_benchmark(policies: dict) -> dict[str, Any]:
    """Run decision policy benchmark."""
    results = {}
    for name, policy in policies.items():
        try:
            metrics = policy.evaluate()
            results[name] = metrics
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


def run_rl_benchmark(policies: dict) -> dict[str, Any]:
    """Run RL policy benchmark."""
    results = {}
    for name, policy in policies.items():
        try:
            returns = policy.evaluate()
            from benchmark.metrics import mean_reward
            results[name] = {"episode_return": mean_reward(returns)}
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


__all__ = ["run_forecast_benchmark", "run_decision_benchmark", "run_rl_benchmark"]

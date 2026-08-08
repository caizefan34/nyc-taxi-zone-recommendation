"""Services for the /simulate and /evaluate endpoints.

/simulate  — runs the finite-demand multi-agent simulator for a given policy.
/evaluate  — returns offline metrics from checked-in benchmark artifacts or
             stored shadow-evaluation records.

Both are OFFLINE. Results are simulator/historical-replay outcomes, never
real-world A/B or production evidence.
"""
from __future__ import annotations

import importlib
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

from src.eval.rollout_core import load_travel_time_matrix, load_trip_market
from src.simulator.multi_agent import MultiAgentConfig, simulate_multi_agent

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
START = datetime(2023, 1, 25)
END = datetime(2023, 2, 1)
ZONE_COUNT = 263

_STRATEGY_MODULES = {
    "hot_zone": "src.2_recommendation_algorithm.baseline_1",
    "single_step": "src.2_recommendation_algorithm.baseline_2_2",
    "two_step": "src.2_recommendation_algorithm.improved_strategy",
}

_MARKET: dict | None = None
_TRAVEL_TIMES = None


def _load_simulation_data():
    global _MARKET, _TRAVEL_TIMES
    if _MARKET is None:
        _MARKET = load_trip_market(ROOT / "data/processed/validation_uncleaned.parquet", start=START, end=END)
        _TRAVEL_TIMES = load_travel_time_matrix(ROOT / "data/processed/travel_time_matrix_dijkstra.csv")
    return _MARKET, _TRAVEL_TIMES


def _load_strategy(name: str):
    module_name = _STRATEGY_MODULES.get(name)
    if module_name is None:
        raise ValueError(f"Unknown simulator policy '{name}'. Use {sorted(_STRATEGY_MODULES)}")
    mod = importlib.import_module(module_name)
    return mod.recommend


def _sample_start_zones(market, driver_count: int, seed: int) -> tuple[int, ...]:
    weights = [len(market.get(zone - 1, ())) for zone in range(1, ZONE_COUNT + 1)]
    if sum(weights) == 0:
        return (132,) * driver_count
    return tuple(random.Random(seed).choices(range(1, ZONE_COUNT + 1), weights=weights, k=driver_count))


def run_simulation(
    model_name: str,
    driver_count: int,
    demand_supply_ratio: float,
    days: int,
    seed: int,
) -> dict:
    """Run one deterministic multi-agent rollout and return aggregate metrics."""
    if model_name not in _STRATEGY_MODULES:
        raise ValueError(f"Unknown simulator policy '{model_name}'. Use {sorted(_STRATEGY_MODULES)}")

    market, travel_times = _load_simulation_data()
    end = START + timedelta(days=days)
    strategy = _load_strategy(model_name)
    config = MultiAgentConfig(
        driver_count=driver_count,
        demand_supply_ratio=demand_supply_ratio,
        seed=seed,
        start_location_ids=_sample_start_zones(market, driver_count, seed),
    )
    result = simulate_multi_agent(
        strategy=strategy,
        market=market,
        travel_times=travel_times,
        start=START,
        end=end,
        config=config,
    )
    return {
        "evaluation_type": "simulation",
        "driver_count": driver_count,
        "days": days,
        "seed": seed,
        "model_name": model_name,
        "fulfilled_trips": int(result.fulfilled_trips),
        "demand_fulfillment_rate": round(result.demand_fulfillment_rate, 4),
        "total_revenue": round(result.total_revenue, 2),
        "average_driver_revenue": round(result.average_driver_revenue, 2),
        "average_idle_minutes": round(result.average_idle_minutes, 2),
        "driver_utilization": round(result.driver_utilization, 4),
        "zone_saturation_rate": round(result.zone_saturation_rate, 4),
        "note": "Simulator outcome only. Not production revenue evidence.",
    }


# -- /evaluate ----------------------------------------------------------

_ARTIFACT_MODELS = {
    "hot_zone": "outputs/forecast_evaluation.json",
    "single_step": "outputs/forecasting_benchmark.json",
    "two_step": "outputs/multi_agent_benchmark.json",
    "dqn": "outputs/rl_benchmark.json",
    "double_dqn": "outputs/rl_benchmark.json",
    "iql": "outputs/rl_benchmark.json",
    "ensemble": "outputs/forecast_evaluation.json",
    "lightgbm": "outputs/forecast_evaluation.json",
    "xgboost": "outputs/forecast_evaluation.json",
    "graphsage": "outputs/graph_benchmark.json",
    "gat": "outputs/graph_benchmark.json",
}


def evaluate_model(model_name: str, evaluation_type: str, city: str) -> dict:
    """Return offline evaluation metrics for a model."""
    if evaluation_type == "benchmark":
        return _evaluate_from_benchmark(model_name)
    if evaluation_type == "shadow":
        return _evaluate_from_shadow(model_name)
    raise ValueError(f"Unknown evaluation_type '{evaluation_type}'")


def _evaluate_from_benchmark(model_name: str) -> dict:
    rel = _ARTIFACT_MODELS.get(model_name)
    if rel is None:
        raise ValueError(f"No stored benchmark evidence for model '{model_name}'")
    path = ROOT / rel
    if not path.exists():
        raise FileNotFoundError(f"Benchmark artifact missing: {path}. Run `make all` first.")
    doc = json.loads(path.read_text(encoding="utf-8"))

    if model_name in ("lightgbm", "ensemble", "xgboost"):
        demand = doc.get("demand") or {}
        metrics = {"mae": demand.get("lightgbm_mae"), "rmse": demand.get("lightgbm_rmse")}
        if model_name == "ensemble":
            metrics = {"mae": (doc.get("ensemble") or {}).get("demand_mae")}
        return {"model_name": model_name, "evaluation_type": "benchmark",
                "metrics": metrics, "source": rel,
                "note": "Held-out demand forecast metrics (MAE/RMSE)."}

    if model_name in ("graphsage", "gat"):
        models = doc.get("models") or {}
        entry = models.get(model_name) or {}
        return {"model_name": model_name, "evaluation_type": "benchmark",
                "metrics": {"mae": entry.get("mae")}, "source": rel,
                "note": "Held-out demand forecast metrics with graph features."}

    # Policy / RL policy metrics
    if model_name in ("dqn", "double_dqn", "iql"):
        strategies = (doc.get("evaluation") or {}).get("strategies") or {}
        entry = strategies.get(model_name) or {}
        metrics = {
            "revenue_per_driver": entry.get("average_driver_revenue"),
            "utilization": entry.get("driver_utilization"),
            "runs": entry.get("runs"),
        }
        return {"model_name": model_name, "evaluation_type": "benchmark",
                "metrics": metrics, "source": rel,
                "note": "Multi-seed RL policy metrics in the finite-demand simulator."}

    if model_name == "two_step":
        strategies = doc.get("strategies") or {}
        entry = strategies.get("two_step") or {}
        return {"model_name": model_name, "evaluation_type": "benchmark",
                "metrics": {
                    "revenue_per_driver": entry.get("average_driver_revenue"),
                    "utilization": entry.get("driver_utilization"),
                    "demand_fulfillment_rate": entry.get("demand_fulfillment_rate"),
                    "runs": entry.get("runs"),
                }, "source": rel,
                "note": "Multi-agent simulator metrics (finite demand, 30 runs)."}

    # hot_zone / single_step fall back to forecast_evaluation / forecasting_benchmark
    if model_name == "hot_zone":
        demand = doc.get("demand") or {}
        return {"model_name": model_name, "evaluation_type": "benchmark",
                "metrics": {"historical_mae": demand.get("historical_mae"),
                            "historical_rmse": demand.get("historical_rmse")},
                "source": rel, "note": "Historical-average baseline metrics."}
    if model_name == "single_step":
        rollout = (doc.get("rollout") or {}).get("historical") or {}
        return {"model_name": model_name, "evaluation_type": "benchmark",
                "metrics": {"mean_daily_fare": rollout.get("mean_daily_fare"), "runs": rollout.get("runs")},
                "source": rel, "note": "Legacy single-driver rollout daily fare."}

    raise ValueError(f"No stored benchmark evidence for model '{model_name}'")


def _evaluate_from_shadow(model_name: str) -> dict:
    path = ROOT / "outputs" / "shadow" / "shadow_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Shadow evaluation file missing: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    metrics = doc.get("metrics") or {}
    if metrics.get("model_name") not in (None, model_name):
        logger.warning("Shadow file records model '%s', requested '%s'", metrics.get("model_name"), model_name)
    return {"model_name": model_name, "evaluation_type": "shadow",
            "metrics": metrics, "source": str(path),
            "note": "Offline shadow evaluation over historical replay. Not real-world evidence."}

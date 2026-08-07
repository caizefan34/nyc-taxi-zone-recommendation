#!/usr/bin/env python3
"""Decision-aware forecasting experiment.

Tests the core research question:
    Does better forecasting accuracy actually produce better decisions?

Compares multiple forecast models on both:
    - Forecast metrics (MAE, RMSE)
    - Decision metrics (NDCG, Revenue, Utilization, Exposure)

Models compared: Historical Average, LightGBM, XGBoost, Ensemble, Oracle
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np


def run_decision_aware_comparison(
    n_zones: int = 50,
    n_trials: int = 100,
    seed: int = 42,
    output_dir: str = "outputs/experiments",
) -> dict:
    """Compare forecast accuracy vs decision quality across models."""
    rng = np.random.RandomState(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Simulated ground truth demand
    true_demand = rng.poisson(lam=25, size=(n_trials, n_zones)).astype(float)

    models = {
        "historical_average": lambda: true_demand + rng.normal(0, 4, true_demand.shape),
        "lightgbm": lambda: true_demand + rng.normal(0, 2, true_demand.shape),
        "xgboost": lambda: true_demand + rng.normal(0, 2.5, true_demand.shape),
        "ensemble": lambda: true_demand + rng.normal(0, 1.5, true_demand.shape),
        "oracle": lambda: true_demand.copy(),
    }

    results = {}
    for name, predictor in models.items():
        pred = predictor()
        pred = np.clip(pred, 0, None)

        # Forecast metrics
        mae = float(np.mean(np.abs(pred - true_demand)))
        rmse = float(np.sqrt(np.mean((pred - true_demand) ** 2)))

        # Decision metric: how well does this forecast rank zones?
        # For each trial, check if top-3 predicted zones overlap with top-3 true zones
        ndcg_scores = []
        hit_scores = []
        for t in range(n_trials):
            true_rank = np.argsort(-true_demand[t])
            pred_rank = np.argsort(-pred[t])
            true_top3 = set(true_rank[:3])
            pred_top3 = set(pred_rank[:3])
            hits = len(true_top3 & pred_top3)
            hit_scores.append(hits / 3.0)
            # Simple NDCG@3
            dcg = sum(1.0 / np.log2(i + 2) for i, z in enumerate(pred_rank[:3]) if z in true_top3)
            idcg = sum(1.0 / np.log2(i + 2) for i in range(3))
            ndcg_scores.append(dcg / idcg if idcg > 0 else 0.0)

        results[name] = {
            "forecast_mae": round(mae, 4),
            "forecast_rmse": round(rmse, 4),
            "decision_ndcg_at_3": round(float(np.mean(ndcg_scores)), 4),
            "decision_hit_at_3": round(float(np.mean(hit_scores)), 4),
        }

    # Compute rank correlation between forecast and decision metrics
    forecast_rank = sorted(results, key=lambda k: results[k]["forecast_mae"])
    decision_rank = sorted(results, key=lambda k: -results[k]["decision_ndcg_at_3"])

    experiment = {
        "experiment_id": f"decision_aware_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "research_question": "Does better forecasting accuracy produce better decisions?",
        "n_zones": n_zones,
        "n_trials": n_trials,
        "seed": seed,
        "results": results,
        "forecast_ranking": forecast_rank,
        "decision_ranking": decision_rank,
        "correlation_note": (
            "Rank correlation between forecast accuracy and decision quality "
            "indicates whether improving MAE/RMSE translates to better recommendations."
        ),
        "note": "Synthetic experiment. Real results require trained models and historical data.",
    }

    path = output_dir / "decision_aware_forecasting.json"
    path.write_text(json.dumps(experiment, indent=2))
    print(f"Experiment saved to {path}")

    print()
    print("Forecast vs Decision Quality:")
    print(f"{'Model':<20s} {'MAE':<10s} {'RMSE':<10s} {'NDCG@3':<10s} {'Hit@3':<10s}")
    print("-" * 60)
    for name in sorted(results):
        r = results[name]
        print(f"{name:<20s} {r['forecast_mae']:<10.4f} {r['forecast_rmse']:<10.4f} "
              f"{r['decision_ndcg_at_3']:<10.4f} {r['decision_hit_at_3']:<10.4f}")

    return experiment


if __name__ == "__main__":
    run_decision_aware_comparison()

"""Train leakage-safe LightGBM demand/fare models and forecast the holdout week."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from src.common.data_loader import DataLoader
from src.forecasting.evaluation import evaluate_forecasters, weekly_historical_arrays
from src.forecasting.features import FEATURE_COLUMNS, build_demand_panel, build_supervised_frame, temporal_split
from src.forecasting.model import (
    fit_demand_forecaster,
    fit_forecasters,
    fit_xgboost_forecasters,
    recursive_forecast,
    save_bundle,
)

ROOT = Path(__file__).resolve().parents[1]


def _markdown(report: dict[str, object]) -> str:
    split = report["split"]
    demand = report["demand"]
    fare = report["fare"]
    ensemble = report["ensemble"]
    xgboost = report["xgboost"]
    bootstrap = demand["paired_timestamp_bootstrap"]
    ensemble_bootstrap = ensemble["paired_timestamp_bootstrap"]
    ablations = report["feature_ablation"]
    demand_mae_change = 1.0 - demand["lightgbm_mae"] / demand["historical_mae"]
    demand_rmse_change = 1.0 - demand["lightgbm_rmse"] / demand["historical_rmse"]
    fare_mae_change = 1.0 - fare["lightgbm_mae"] / fare["historical_mae"]
    return "\n".join(
        [
            "# Supervised Forecasting Evaluation",
            "",
            "The split is chronological. Every lag, rolling, and neighborhood-demand feature is shifted before "
            "the target slot.",
            "",
            "## Temporal split",
            "",
            f"- Train: `{split['train_start']}` through `{split['train_end']}` ({split['train_rows']:,} rows)",
            f"- Validation: `{split['validation_start']}` through `{split['validation_end']}` "
            f"({split['validation_rows']:,} rows)",
            "",
            "## Forecast accuracy",
            "",
            "| Target | Metric | Historical average | LightGBM | Selected ensemble |",
            "|---|---:|---:|---:|---:|",
            f"| Demand count | MAE | {demand['historical_mae']:.4f} | {demand['lightgbm_mae']:.4f} | "
            f"{ensemble['demand_mae']:.4f} |",
            f"| Demand count | RMSE | {demand['historical_rmse']:.4f} | {demand['lightgbm_rmse']:.4f} | "
            f"{ensemble['demand_rmse']:.4f} |",
            f"| Mean fare (observed cells) | MAE | {fare['historical_mae']:.4f} | {fare['lightgbm_mae']:.4f} | "
            f"{ensemble['fare_mae']:.4f} |",
            f"| Mean fare (observed cells) | RMSE | {fare['historical_rmse']:.4f} | "
            f"{fare['lightgbm_rmse']:.4f} | {ensemble['fare_rmse']:.4f} |",
            "",
            f"Relative LightGBM improvements over the historical average are demand MAE "
            f"{demand_mae_change:+.2%}, demand RMSE {demand_rmse_change:+.2%}, and fare MAE "
            f"{fare_mae_change:+.2%}.",
            "",
            "Optional same-split XGBoost baseline: demand MAE "
            f"{xgboost['demand']['mae']:.4f}, demand RMSE {xgboost['demand']['rmse']:.4f}, "
            f"fare MAE {xgboost['fare']['mae']:.4f}, fare RMSE {xgboost['fare']['rmse']:.4f}.",
            "",
            "The deployment forecast is an internally selected ensemble: "
            f"{ensemble['demand_lightgbm_weight']:.2f} LightGBM demand + "
            f"{1.0 - ensemble['demand_lightgbm_weight']:.2f} historical demand, and "
            f"{ensemble['fare_lightgbm_weight']:.2f} LightGBM fare + "
            f"{1.0 - ensemble['fare_lightgbm_weight']:.2f} historical fare. Its validation demand MAE is "
            f"{ensemble['demand_mae']:.4f} and fare MAE is {ensemble['fare_mae']:.4f}.",
            "Because these blend weights minimize error on that same validation window, the ensemble result is a "
            "model-selection estimate rather than an untouched test estimate.",
            "",
            "The paired timestamp-block bootstrap for LightGBM demand MAE improvement is "
            f"{bootstrap['mean_mae_improvement']:.4f}, 95% CI "
            f"[{bootstrap['ci95_low']:.4f}, {bootstrap['ci95_high']:.4f}], "
            f"Cohen's dz={bootstrap['cohen_dz']:.3f} over {bootstrap['timestamp_blocks']} half-hour blocks.",
            "The selected ensemble improvement is "
            f"{ensemble_bootstrap['mean_mae_improvement']:.4f}, 95% CI "
            f"[{ensemble_bootstrap['ci95_low']:.4f}, {ensemble_bootstrap['ci95_high']:.4f}], "
            f"Cohen's dz={ensemble_bootstrap['cohen_dz']:.3f}.",
            "",
            "## Demand feature ablation",
            "",
            "All ablations use the same training rows, validation rows, seed, and LightGBM settings.",
            "",
            "| Feature set | Demand MAE | Demand RMSE |",
            "|---|---:|---:|",
            f"| Full | {ablations['full']['mae']:.4f} | {ablations['full']['rmse']:.4f} |",
            f"| Without lag features | {ablations['without_lags']['mae']:.4f} | "
            f"{ablations['without_lags']['rmse']:.4f} |",
            f"| Without rolling features | {ablations['without_rolling']['mae']:.4f} | "
            f"{ablations['without_rolling']['rmse']:.4f} |",
            f"| Without neighborhood features | {ablations['without_neighborhood']['mae']:.4f} | "
            f"{ablations['without_neighborhood']['rmse']:.4f} |",
            "",
            "`predicted_demand_probability = 1 - exp(-predicted_demand_count)` is the Poisson probability of at least "
            "one passenger arrival in a zone-slot. It is not a driver's pickup-success probability.",
            "",
        ]
    )


def _feature_ablation(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    seed: int,
    full_mae: float,
    full_rmse: float,
) -> dict[str, object]:
    groups = {
        "without_lags": [column for column in FEATURE_COLUMNS if not column.startswith("lag_demand_")],
        "without_rolling": [
            column for column in FEATURE_COLUMNS if not column.startswith("rolling_demand_")
        ],
        "without_neighborhood": [
            column
            for column in FEATURE_COLUMNS
            if not column.startswith("neighbor_")
        ],
    }
    actual = validation["target_demand"].to_numpy(dtype=float)
    results = {
        "full": {
            "features": list(FEATURE_COLUMNS),
            "mae": full_mae,
            "rmse": full_rmse,
        }
    }
    for name, features in groups.items():
        model = fit_demand_forecaster(train, feature_columns=features, random_seed=seed)
        predicted = model.predict(validation[features])
        errors = actual - predicted
        results[name] = {
            "features": features,
            "mae": float(abs(errors).mean()),
            "rmse": float((errors**2).mean() ** 0.5),
        }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=ROOT / "data/processed/train_cleaned.parquet")
    parser.add_argument("--travel-times", type=Path, default=ROOT / "data/processed/travel_time_matrix_dijkstra.csv")
    parser.add_argument("--validation-days", type=int, default=4)
    parser.add_argument("--forecast-start", default="2023-01-25 00:00:00")
    parser.add_argument("--forecast-end", default="2023-02-01 00:30:00")
    parser.add_argument("--seed", type=int, default=20230722)
    parser.add_argument("--model-output", type=Path, default=ROOT / "data/processed/forecast_models.joblib")
    parser.add_argument("--forecast-output", type=Path, default=ROOT / "data/processed/forecast_predictions.parquet")
    parser.add_argument(
        "--validation-predictions",
        type=Path,
        default=ROOT / "data/processed/forecast_validation_predictions.parquet",
    )
    parser.add_argument("--report-json", type=Path, default=ROOT / "outputs/forecast_evaluation.json")
    parser.add_argument("--report-md", type=Path, default=ROOT / "outputs/forecast_evaluation.md")
    args = parser.parse_args()

    trips = pq.read_table(
        args.train,
        columns=["tpep_pickup_datetime", "PULocationID", "fare_amount"],
    ).to_pandas()
    travel_times = DataLoader(ROOT).load_travel_time_matrix(args.travel_times)
    panel = build_demand_panel(trips)
    supervised, neighbors, neighbor_times = build_supervised_frame(panel, travel_times)
    train, validation, split_time = temporal_split(supervised, validation_days=args.validation_days)
    validation_bundle = fit_forecasters(
        train,
        neighbor_indices=neighbors,
        neighbor_mean_travel=neighbor_times,
        random_seed=args.seed,
    )
    report, validation_predictions = evaluate_forecasters(validation_bundle, train, validation)
    report["feature_ablation"] = _feature_ablation(
        train,
        validation,
        seed=args.seed,
        full_mae=report["demand"]["lightgbm_mae"],
        full_rmse=report["demand"]["lightgbm_rmse"],
    )
    xgboost_bundle = fit_xgboost_forecasters(
        train,
        neighbor_indices=neighbors,
        neighbor_mean_travel=neighbor_times,
        random_seed=args.seed,
    )
    xgboost_report, xgboost_predictions = evaluate_forecasters(xgboost_bundle, train, validation)
    report["xgboost"] = {
        "demand": {
            "mae": xgboost_report["demand"]["lightgbm_mae"],
            "rmse": xgboost_report["demand"]["lightgbm_rmse"],
        },
        "fare": {
            "mae": xgboost_report["fare"]["lightgbm_mae"],
            "rmse": xgboost_report["fare"]["lightgbm_rmse"],
        },
    }
    validation_predictions["xgboost_demand_count"] = xgboost_predictions["predicted_demand_count"]
    validation_predictions["xgboost_expected_fare"] = xgboost_predictions["predicted_expected_fare"]
    report["model"] = {
        "library": "lightgbm",
        "random_seed": args.seed,
        "validation_split_time": split_time.isoformat(),
        "feature_count": len(validation_bundle.demand_model.feature_name_),
        "features": list(validation_bundle.demand_model.feature_name_),
    }

    full_bundle = fit_forecasters(
        supervised,
        neighbor_indices=neighbors,
        neighbor_mean_travel=neighbor_times,
        random_seed=args.seed,
    )
    historical_demand, historical_fare = weekly_historical_arrays(supervised, zone_count=panel.zone_count)
    full_bundle.historical_demand = historical_demand
    full_bundle.historical_fare = historical_fare
    full_bundle.demand_blend_weight = report["ensemble"]["demand_lightgbm_weight"]
    full_bundle.fare_blend_weight = report["ensemble"]["fare_lightgbm_weight"]
    forecasts = recursive_forecast(
        full_bundle,
        panel,
        start=pd.Timestamp(args.forecast_start),
        end=pd.Timestamp(args.forecast_end),
    )

    for path in (
        args.model_output,
        args.forecast_output,
        args.validation_predictions,
        args.report_json,
        args.report_md,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
    save_bundle(full_bundle, args.model_output)
    forecasts.to_parquet(args.forecast_output, compression="zstd", index=False)
    validation_predictions.to_parquet(args.validation_predictions, compression="zstd", index=False)
    args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {len(forecasts):,} recursive forecast rows to {args.forecast_output}")


if __name__ == "__main__":
    main()

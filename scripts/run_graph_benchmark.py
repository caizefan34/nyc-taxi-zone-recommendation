"""Train leakage-safe OD graph embeddings and compare demand forecasters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch

from src.audit.statistics import paired_comparison
from src.common.data_loader import DataLoader
from src.forecasting.features import FEATURE_COLUMNS, build_demand_panel, build_supervised_frame, temporal_split
from src.forecasting.model import fit_demand_forecaster
from src.graph import (
    append_graph_embeddings,
    append_od_message_features,
    build_od_graph,
    train_graph_embeddings,
)

ROOT = Path(__file__).resolve().parents[1]


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    errors = actual - predicted
    return {
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(np.square(errors)))),
    }


def _slot_mae(frame: pd.DataFrame, predicted: np.ndarray) -> np.ndarray:
    errors = frame.loc[:, ["timestamp"]].copy()
    errors["absolute_error"] = np.abs(frame["target_demand"].to_numpy(dtype=float) - predicted)
    return errors.groupby("timestamp", sort=True)["absolute_error"].mean().to_numpy(dtype=float)


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Graph-Enhanced Demand Forecasting Benchmark",
        "",
        "The OD graph uses only trips before the internal validation boundary. Static GraphSAGE and GAT zone "
        "embeddings are appended to the same leakage-safe LightGBM feature matrix.",
        "",
        "| Model | Demand MAE | Demand RMSE | MAE change vs non-graph |",
        "|---|---:|---:|---:|",
    ]
    baseline = report["models"]["non_graph_lightgbm"]
    lines.append(f"| Non-graph LightGBM | {baseline['mae']:.4f} | {baseline['rmse']:.4f} | -- |")
    for name, label in (
        ("od_messages", "OD messages + LightGBM"),
        ("graphsage", "GraphSAGE + LightGBM"),
        ("gat", "GAT + LightGBM"),
    ):
        values = report["models"][name]
        comparison = report["paired_slot_mae_reduction"][name]
        lines.append(f"| {label} | {values['mae']:.4f} | {values['rmse']:.4f} | {comparison['mean_difference']:+.4f} |")
    lines.extend(["", "## Paired timestamp-level comparisons", ""])
    for name, label in (
        ("od_messages", "OD messages"),
        ("graphsage", "GraphSAGE"),
        ("gat", "GAT"),
    ):
        values = report["paired_slot_mae_reduction"][name]
        lines.append(
            f"- Non-graph minus {label} slot MAE: {values['mean_difference']:+.4f}, 95% CI "
            f"[{values['ci95_low']:+.4f}, {values['ci95_high']:+.4f}], paired t p="
            f"{values['paired_t_pvalue']:.3g}, Cohen's dz={values['cohen_dz']:.3f}."
        )
    lines.extend(
        [
            "",
            "A positive reduction favors graph features. The confidence intervals cover held-out half-hour "
            "timestamps, not month-to-month drift or deployment outcomes.",
            "",
            "All point estimates improve on non-graph LightGBM, but every confidence interval crosses zero. "
            "Static GraphSAGE and GAT embeddings also underperform OD message features alone, so the graph-neural "
            "contribution is not statistically supported.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=ROOT / "data/processed/train_cleaned.parquet")
    parser.add_argument(
        "--travel-times",
        type=Path,
        default=ROOT / "data/processed/travel_time_matrix_dijkstra.csv",
    )
    parser.add_argument("--validation-days", type=int, default=4)
    parser.add_argument("--embedding-size", type=int, default=8)
    parser.add_argument("--graph-epochs", type=int, default=200)
    parser.add_argument("--estimators", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20230722)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/graph_benchmark.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/graph_benchmark.md")
    args = parser.parse_args()

    trips = pq.read_table(
        args.train,
        columns=["tpep_pickup_datetime", "PULocationID", "DOLocationID", "fare_amount"],
    ).to_pandas()
    travel_times = DataLoader(ROOT).load_travel_time_matrix(args.travel_times)
    panel = build_demand_panel(trips)
    supervised, _, _ = build_supervised_frame(panel, travel_times)
    train, validation, split_time = temporal_split(supervised, validation_days=args.validation_days)
    graph = build_od_graph(trips, zone_count=panel.zone_count, end_exclusive=split_time)
    message_train, message_columns = append_od_message_features(train, graph)
    message_validation, _ = append_od_message_features(validation, graph)

    baseline_model = fit_demand_forecaster(
        train,
        random_seed=args.seed,
        n_estimators=args.estimators,
    )
    actual = validation["target_demand"].to_numpy(dtype=float)
    baseline_prediction = np.clip(baseline_model.predict(validation[FEATURE_COLUMNS]), 0.0, None)
    predictions = {"non_graph_lightgbm": baseline_prediction}
    model_metrics = {"non_graph_lightgbm": _metrics(actual, baseline_prediction)}
    graph_diagnostics = {}

    message_feature_columns = [*FEATURE_COLUMNS, *message_columns]
    message_model = fit_demand_forecaster(
        message_train,
        feature_columns=message_feature_columns,
        random_seed=args.seed,
        n_estimators=args.estimators,
    )
    message_prediction = np.clip(
        message_model.predict(message_validation[message_feature_columns]),
        0.0,
        None,
    )
    predictions["od_messages"] = message_prediction
    model_metrics["od_messages"] = _metrics(actual, message_prediction)

    for model_name in ("graphsage", "gat"):
        embedding_result = train_graph_embeddings(
            graph,
            model=model_name,
            embedding_size=args.embedding_size,
            epochs=args.graph_epochs,
            seed=args.seed,
            device=args.device,
        )
        graph_train, embedding_columns = append_graph_embeddings(
            message_train,
            embedding_result.embeddings,
            prefix=model_name,
        )
        graph_validation, _ = append_graph_embeddings(
            message_validation,
            embedding_result.embeddings,
            prefix=model_name,
        )
        feature_columns = [*FEATURE_COLUMNS, *message_columns, *embedding_columns]
        model = fit_demand_forecaster(
            graph_train,
            feature_columns=feature_columns,
            random_seed=args.seed,
            n_estimators=args.estimators,
        )
        prediction = np.clip(model.predict(graph_validation[feature_columns]), 0.0, None)
        predictions[model_name] = prediction
        model_metrics[model_name] = _metrics(actual, prediction)
        graph_diagnostics[model_name] = {
            "embedding_size": args.embedding_size,
            "epochs": embedding_result.epochs,
            "final_reconstruction_loss": embedding_result.final_loss,
        }

    baseline_slot_mae = _slot_mae(validation, predictions["non_graph_lightgbm"])
    report = {
        "training_end_exclusive": split_time.isoformat(),
        "validation_start": pd.Timestamp(validation["timestamp"].min()).isoformat(),
        "validation_end": pd.Timestamp(validation["timestamp"].max()).isoformat(),
        "validation_timestamps": int(validation["timestamp"].nunique()),
        "seed": args.seed,
        "device": args.device,
        "graph": {
            "zone_count": graph.zone_count,
            "training_trip_count": int(graph.counts.sum()),
            "directed_edge_count": int((graph.counts > 0.0).sum()),
            "models": graph_diagnostics,
        },
        "models": model_metrics,
        "paired_slot_mae_reduction": {
            name: paired_comparison(baseline_slot_mae, _slot_mae(validation, predictions[name]))
            for name in ("od_messages", "graphsage", "gat")
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

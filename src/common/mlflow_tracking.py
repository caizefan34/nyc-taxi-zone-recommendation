"""MLflow experiment tracking setup."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

try:
    import mlflow
except ImportError:
    mlflow = None


@contextmanager
def init_mlflow(
    experiment_name: str = "nyc_taxi_zone",
    tracking_uri: str | None = None,
    run_name: str | None = None,
    tags: dict[str, Any] | None = None,
):
    """Initialize an MLflow run with consistent defaults."""
    if mlflow is None:
        print("MLflow not installed. Install with: pip install mlflow")
        yield None
        return
    uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        if tags:
            mlflow.set_tags(tags)
        yield run


def log_metrics(metrics: dict[str, float], step: int | None = None) -> None:
    if mlflow is None:
        return
    mlflow.log_metrics(metrics, step=step)


def log_params(params: dict[str, Any]) -> None:
    if mlflow is None:
        return
    mlflow.log_params(params)


def log_artifact(path: str) -> None:
    if mlflow is None:
        return
    mlflow.log_artifact(path)

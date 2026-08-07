"""Observability — metrics abstraction and structured logging.

Supports both simple in-memory metrics and optional Prometheus integration.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PredictionMetrics:
    """Metrics for recommendation/inference operations."""

    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0
    recommendations_by_zone: dict[int, int] = field(default_factory=dict)
    recommendations_by_model: dict[str, int] = field(default_factory=dict)

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record_request(
        self,
        latency_ms: float,
        model_name: str,
        recommended_zone: int,
        error: bool = False,
    ) -> None:
        with self._lock:
            self.total_requests += 1
            self.total_latency_ms += latency_ms
            if error:
                self.total_errors += 1
            self.recommendations_by_model[model_name] = (
                self.recommendations_by_model.get(model_name, 0) + 1
            )
            self.recommendations_by_zone[recommended_zone] = (
                self.recommendations_by_zone.get(recommended_zone, 0) + 1
            )

    def snapshot(self) -> dict:
        with self._lock:
            avg_latency = (
                round(self.total_latency_ms / self.total_requests, 2)
                if self.total_requests else 0.0
            )
            return {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate": round(self.total_errors / self.total_requests, 4) if self.total_requests else 0.0,
                "avg_latency_ms": avg_latency,
                "recommendations_by_model": dict(self.recommendations_by_model),
                "top_recommended_zones": {
                    str(k): v for k, v in
                    sorted(self.recommendations_by_zone.items(), key=lambda x: -x[1])[:10]
                },
            }


_global_metrics = PredictionMetrics()


def get_metrics() -> PredictionMetrics:
    """Get the global metrics collector."""
    return _global_metrics


def metrics_snapshot() -> dict:
    """Return a snapshot of current metrics."""
    return _global_metrics.snapshot()


def export_metrics_json(path: str | Path) -> None:
    """Export current metrics to a JSON file."""
    Path(path).write_text(json.dumps(metrics_snapshot(), indent=2))

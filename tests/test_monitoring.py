"""Tests for observability metrics."""
from __future__ import annotations

from src.monitoring.metrics import PredictionMetrics, get_metrics, metrics_snapshot


class TestPredictionMetrics:
    def test_record_request(self):
        metrics = PredictionMetrics()
        metrics.record_request(
            latency_ms=5.2,
            model_name="two_step",
            recommended_zone=132,
        )
        metrics.record_request(
            latency_ms=3.1,
            model_name="two_step",
            recommended_zone=132,
        )
        assert metrics.total_requests == 2
        assert metrics.total_errors == 0

    def test_snapshot(self):
        metrics = PredictionMetrics()
        metrics.record_request(
            latency_ms=5.0,
            model_name="two_step",
            recommended_zone=132,
        )
        snap = metrics.snapshot()
        assert snap["total_requests"] == 1
        assert snap["avg_latency_ms"] == 5.0
        assert snap["error_rate"] == 0.0

    def test_error_recording(self):
        metrics = PredictionMetrics()
        metrics.record_request(latency_ms=1.0, model_name="test", recommended_zone=1, error=True)
        metrics.record_request(latency_ms=1.0, model_name="test", recommended_zone=1, error=True)
        metrics.record_request(latency_ms=1.0, model_name="test", recommended_zone=1, error=False)
        snap = metrics.snapshot()
        assert snap["total_errors"] == 2
        assert abs(snap["error_rate"] - 2/3) < 0.001

    def test_zone_distribution(self):
        metrics = PredictionMetrics()
        for _ in range(5):
            metrics.record_request(latency_ms=1.0, model_name="test", recommended_zone=132)
        for _ in range(3):
            metrics.record_request(latency_ms=1.0, model_name="test", recommended_zone=236)
        snap = metrics.snapshot()
        top = snap["top_recommended_zones"]
        assert "132" in top
        assert top["132"] == 5


def test_global_metrics():
    m = get_metrics()
    assert isinstance(m, PredictionMetrics)


def test_metrics_snapshot():
    snap = metrics_snapshot()
    assert "total_requests" in snap
    assert "avg_latency_ms" in snap

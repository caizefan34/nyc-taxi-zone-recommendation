"""Tests for shadow evaluation."""
from __future__ import annotations

from datetime import datetime

from src.evaluation.shadow.evaluator import ShadowEvaluator, ShadowRecord


class TestShadowRecord:
    def test_creation(self):
        rec = ShadowRecord(
            timestamp="2023-01-15T18:30:00",
            vehicle_id="v1",
            current_zone=161,
            recommended_zone=132,
            model_name="two_step",
            model_version="v1",
        )
        assert rec.vehicle_id == "v1"
        assert rec.recommended_zone == 132

    def test_to_dict(self):
        rec = ShadowRecord(
            timestamp="2023-01-15T18:30:00",
            vehicle_id="v1",
            current_zone=161,
            recommended_zone=132,
        )
        d = rec.to_dict()
        assert d["vehicle_id"] == "v1"
        assert d["evaluation_type"] == "historical_replay"


class TestShadowEvaluator:
    def test_record_recommendation(self):
        evaluator = ShadowEvaluator()
        evaluator.record_recommendation(
            vehicle_id="v1",
            timestamp=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            recommended_zone=132,
            model_name="two_step",
            model_version="v1",
        )
        assert len(evaluator._records) == 1

    def test_record_actual(self):
        evaluator = ShadowEvaluator()
        evaluator.record_recommendation(
            vehicle_id="v1",
            timestamp=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            recommended_zone=132,
        )
        evaluator.record_actual(
            vehicle_id="v1",
            actual_zone=236,
        )
        assert evaluator._records[0].actual_next_zone == 236

    def test_compute_metrics_empty(self):
        evaluator = ShadowEvaluator()
        metrics = evaluator.compute_metrics()
        assert metrics.total_records == 0

    def test_compute_metrics_with_data(self):
        evaluator = ShadowEvaluator()
        for i in range(10):
            evaluator.record_recommendation(
                vehicle_id=f"v{i}",
                timestamp=datetime(2023, 1, 15, 18, 30),
                current_zone=161,
                recommended_zone=132 if i < 5 else 236,
                predicted_revenue=25.0,
                model_name="two_step",
                model_version="v1",
            )
            evaluator.record_actual(
                vehicle_id=f"v{i}",
                actual_zone=132 if i < 3 else 236,
                actual_revenue=22.0 if i < 5 else 28.0,
            )
        metrics = evaluator.compute_metrics()
        assert metrics.total_records == 10
        assert metrics.recommendation_acceptance is not None

    def test_save(self, tmp_path):
        evaluator = ShadowEvaluator(output_dir=tmp_path)
        evaluator.record_recommendation(
            vehicle_id="v1",
            timestamp=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            recommended_zone=132,
        )
        path = evaluator.save()
        assert path.exists()

"""Tests for the /simulate and /evaluate API endpoints."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from src.api.main import app  # noqa: E402
from src.api.services.simulation_service import evaluate_model  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestSimulateEndpoint:
    def test_simulate_returns_simulator_metrics(self, client):
        r = client.post("/simulate", json={
            "model_name": "hot_zone", "driver_count": 10, "days": 1, "seed": 1,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["evaluation_type"] == "simulation"
        assert data["model_name"] == "hot_zone"
        assert data["average_driver_revenue"] >= 0
        assert data["note"] == "Simulator outcome only. Not production revenue evidence."

    def test_simulate_is_deterministic(self, client):
        a = client.post("/simulate", json={"model_name": "hot_zone", "driver_count": 10, "days": 1, "seed": 42})
        b = client.post("/simulate", json={"model_name": "hot_zone", "driver_count": 10, "days": 1, "seed": 42})
        assert a.json()["fulfilled_trips"] == b.json()["fulfilled_trips"]

    def test_simulate_rejects_unknown_policy(self, client):
        r = client.post("/simulate", json={"model_name": "nope", "driver_count": 5, "days": 1, "seed": 1})
        assert r.status_code == 400

    def test_simulate_rejects_bad_payload(self, client):
        r = client.post("/simulate", json={"model_name": "hot_zone", "driver_count": 0})
        assert r.status_code == 422


class TestEvaluateEndpoint:
    def test_evaluate_policy(self, client):
        r = client.post("/evaluate", json={"model_name": "two_step", "evaluation_type": "benchmark"})
        assert r.status_code == 200
        data = r.json()
        assert data["model_name"] == "two_step"
        assert "revenue_per_driver" in data["metrics"]
        assert data["evaluation_type"] == "benchmark"

    def test_evaluate_forecast(self, client):
        r = client.post("/evaluate", json={"model_name": "lightgbm", "evaluation_type": "benchmark"})
        assert r.status_code == 200
        assert "mae" in r.json()["metrics"]

    def test_evaluate_unknown_model(self, client):
        r = client.post("/evaluate", json={"model_name": "does_not_exist", "evaluation_type": "benchmark"})
        assert r.status_code == 400

    def test_evaluate_shadow_records(self, client):
        # A shadow evaluation file is checked in (v3.5 historical replay). Expect 200 with records.
        r = client.post("/evaluate", json={"model_name": "two_step", "evaluation_type": "shadow"})
        assert r.status_code == 200
        data = r.json()
        assert data["evaluation_type"] == "shadow"
        assert data["metrics"].get("total_records", 0) > 0

    def test_evaluate_invalid_type(self, client):
        r = client.post("/evaluate", json={"model_name": "two_step", "evaluation_type": "bogus"})
        assert r.status_code == 422


class TestEvaluateService:
    def test_evaluate_service_policy(self):
        result = evaluate_model("two_step", "benchmark", "nyc")
        assert result["metrics"]["revenue_per_driver"] > 0

    def test_evaluate_service_unknown(self):
        with pytest.raises(ValueError):
            evaluate_model("missing", "benchmark", "nyc")

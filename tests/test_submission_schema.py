"""Test benchmark submission schema validation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_schema_is_valid_json():
    schema_path = ROOT / "benchmark" / "schemas" / "result_schema.json"
    content = schema_path.read_text(encoding="utf-8")
    schema = json.loads(content)
    assert schema["title"] == "BenchmarkResult"
    assert "$schema" in schema
    assert "properties" in schema


def test_schema_requires_model_name():
    schema_path = ROOT / "benchmark" / "schemas" / "result_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert "model" in schema["required"]
    model_props = schema["properties"]["model"]["properties"]
    assert "name" in model_props


def test_schema_has_all_metric_categories():
    schema_path = ROOT / "benchmark" / "schemas" / "result_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    metrics = schema["properties"]["metrics"]["properties"]
    assert "forecast" in metrics
    assert "decision" in metrics
    assert "rl" in metrics
    assert "deployment" in metrics


def test_schema_has_reproducibility():
    schema_path = ROOT / "benchmark" / "schemas" / "result_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert "reproducibility" in schema["properties"]

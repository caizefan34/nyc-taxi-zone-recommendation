"""Test external model runner."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.runners.run_external_model import load_model_class, run_benchmark  # noqa: E402


def test_load_example_policy():
    model_path = str(ROOT / "examples" / "custom_policy_example.py")
    cls = load_model_class(model_path, "TimeBasedPolicy")
    assert cls.__name__ == "TimeBasedPolicy"


def test_load_nonexistent_file():
    with pytest.raises((ImportError, FileNotFoundError)):
        load_model_class("nonexistent.py", "Fake")


def test_run_benchmark_on_example_policy():
    model_path = str(ROOT / "examples" / "custom_policy_example.py")
    cls = load_model_class(model_path, "TimeBasedPolicy")
    result = run_benchmark(cls, "policy")
    assert result["model"]["name"] == "TimeBasedPolicy"
    assert result["model"]["type"] == "policy"
    assert "metrics" in result
    assert "decision" in result["metrics"]
    assert result["metrics"]["decision"]["revenue_per_driver"] == 480.0


def test_benchmark_output_is_valid_json():
    model_path = str(ROOT / "examples" / "custom_policy_example.py")
    cls = load_model_class(model_path, "TimeBasedPolicy")
    result = run_benchmark(cls, "policy")
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    assert parsed["benchmark_version"] == "2.0.0"
    assert "timestamp" in parsed


def test_result_matches_schema():
    schema_path = ROOT / "benchmark" / "schemas" / "result_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    model_path = str(ROOT / "examples" / "custom_policy_example.py")
    cls = load_model_class(model_path, "TimeBasedPolicy")
    result = run_benchmark(cls, "policy")
    # Validate required fields
    for field in schema["required"]:
        assert field in result, f"Missing required field: {field}"
    assert result["model"]["name"] is not None
    assert result["model"]["type"] in schema["properties"]["model"]["properties"]["type"]["enum"]

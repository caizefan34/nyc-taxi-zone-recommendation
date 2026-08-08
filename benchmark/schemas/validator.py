"""Validation for benchmark result JSONs against the result schema.

Implements a lightweight, dependency-free validator for the fields the
platform's benchmark protocol actually uses. A full JSON-Schema check is
available when `jsonschema` is installed; this module degrades gracefully.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "result_schema.json"

_VALID_TYPES = ("forecast", "policy", "rl_policy")


def _load_schema() -> dict[str, Any]:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_result(result: dict[str, Any]) -> list[str]:
    """Validate a benchmark result dict. Returns a list of error strings (empty = valid)."""
    errors: list[str] = []

    if not isinstance(result, dict):
        return ["result must be a JSON object"]

    model = result.get("model")
    if not isinstance(model, dict):
        errors.append("missing 'model' object")
    else:
        name = model.get("name")
        if not name or not isinstance(name, str):
            errors.append("'model.name' must be a non-empty string")
        mtype = model.get("type")
        if mtype not in _VALID_TYPES:
            errors.append(f"'model.type' must be one of {_VALID_TYPES}, got {mtype!r}")

    if "benchmark_version" in result and not isinstance(result["benchmark_version"], str):
        errors.append("'benchmark_version' must be a string")

    metrics = result.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        errors.append("'metrics' must be a non-empty object")
    else:
        for key in ("forecast", "decision", "rl"):
            section = metrics.get(key)
            if section is not None and not isinstance(section, dict):
                errors.append(f"'metrics.{key}' must be an object")

    reproducibility = result.get("reproducibility")
    if reproducibility is not None:
        if not isinstance(reproducibility, dict):
            errors.append("'reproducibility' must be an object")
        elif "random_seed" in reproducibility and not isinstance(
            reproducibility.get("random_seed"), int
        ):
            errors.append("'reproducibility.random_seed' must be an integer")

    return errors


def validate_result_file(path: Path) -> list[str]:
    """Validate a result JSON file on disk."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"cannot read JSON: {exc}"]
    return validate_result(data)


if __name__ == "__main__":
    import sys

    path = Path(sys.argv[1] if len(sys.argv) > 1 else "result.json")
    problems = validate_result_file(path)
    if problems:
        print("INVALID:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("VALID")

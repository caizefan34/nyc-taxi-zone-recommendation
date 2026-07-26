#!/usr/bin/env python3
"""Run benchmark on an external model.

Usage:
    python benchmark/runners/run_external_model.py --model-path path/to/model.py --model-class MyPolicy
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def load_model_class(model_path: str, class_name: str):
    spec = importlib.util.spec_from_file_location("external_model", model_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load: {model_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def run_benchmark(model_cls, model_type: str) -> dict:
    model = model_cls()
    result = {
        "model": {"name": model_cls.__name__, "version": "external", "type": model_type},
        "benchmark_version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {},
        "reproducibility": {"random_seed": 42},
    }
    try:
        metrics = model.evaluate()
        if model_type == "policy":
            result["metrics"]["decision"] = metrics
        elif model_type == "forecast":
            result["metrics"]["forecast"] = metrics
        elif model_type == "rl_policy":
            result["metrics"]["rl"] = metrics
    except Exception as e:
        result["error"] = str(e)
    return result


def main():
    parser = argparse.ArgumentParser(description="Run benchmark on external model")
    parser.add_argument("--model-path", required=True, help="Path to Python file with model class")
    parser.add_argument("--model-class", required=True, help="Name of model class")
    parser.add_argument("--model-type", default="policy", choices=["forecast", "policy", "rl_policy"])
    parser.add_argument("--output", default="outputs/external_result.json", help="Output JSON path")
    args = parser.parse_args()

    model_cls = load_model_class(args.model_path, args.model_class)
    result = run_benchmark(model_cls, args.model_type)

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    print(f"Benchmark complete. Result saved to {output_path}")
    if "error" in result:
        print(f"Warning: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

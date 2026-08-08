#!/usr/bin/env python3
"""Urban Mobility Intelligence Benchmark — unified CLI.

A single entry point to run a model on a city and regenerate the leaderboard.

Usage:
    python benchmark/run.py --model two_step --city nyc
    python benchmark/run.py --model graphsage --city nyc --seed 42
    python benchmark/run.py --model my_policy --city nyc --source outputs/my_results.json
    python benchmark/run.py --leaderboard            # regenerate leaderboard from stored results
    python benchmark/run.py --list                   # list supported models and cities

Model sources (in priority order):
    1. `--source PATH`  : a precomputed result JSON (validated against the result schema)
    2. internal         : a known baseline evaluated from checked-in `outputs/*.json`
    3. external         : a model implementing `src.interfaces.Policy/ForecastModel/RLPolicy`,
                          loaded via --model-path/--model-class (reuses run_external_model.py)

All metrics are SIMULATOR / HISTORICAL-REPLAY outcomes unless stated otherwise.
This tool does NOT provide production revenue or real-world A/B evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.schemas.validator import validate_result  # noqa: E402

# Known internal baselines -> source output files that contain their metrics.
# Kept as a stable registry so `run.py` stays a thin orchestrator over existing
# benchmark artifacts instead of re-training models on every invocation.
INTERNAL_MODELS: dict[str, dict[str, str]] = {
    "hot_zone": {"output": "outputs/forecast_evaluation.json", "type": "policy"},
    "single_step": {"output": "outputs/forecasting_benchmark.json", "type": "policy"},
    "two_step": {"output": "outputs/multi_agent_benchmark.json", "type": "policy"},
    "dqn": {"output": "outputs/rl_benchmark.json", "type": "rl_policy"},
    "double_dqn": {"output": "outputs/rl_benchmark.json", "type": "rl_policy"},
    "iql": {"output": "outputs/rl_benchmark.json", "type": "rl_policy"},
    "ensemble": {"output": "outputs/forecast_evaluation.json", "type": "forecast"},
    "lightgbm": {"output": "outputs/forecast_evaluation.json", "type": "forecast"},
    "xgboost": {"output": "outputs/forecast_evaluation.json", "type": "forecast"},
    "graphsage": {"output": "outputs/graph_benchmark.json", "type": "forecast"},
    "gat": {"output": "outputs/graph_benchmark.json", "type": "forecast"},
}

SUPPORTED_CITIES = ("nyc", "chicago", "london", "singapore")


def _resolve_output_file(root: Path, name: str) -> Path:
    """Resolve an internal model name to a source JSON path, with fallbacks."""
    candidate = root / name
    if candidate.exists():
        return candidate
    for suffix in (".json",):
        if (root / f"{name}{suffix}").exists():
            return root / f"{name}{suffix}"
    raise FileNotFoundError(f"Could not locate output artifact for model '{name}'. "
                            "Run `make all` first, or pass --source PATH.")


def load_source_result(root: Path, model: str) -> dict:
    """Load a stored benchmark artifact for an internal baseline.

    Internal artifacts are the platform's own checked-in benchmark snapshots
    (validated by their own audit tests); they are not result-schema submission
    documents, so schema validation is intentionally not applied here.
    """
    spec = INTERNAL_MODELS.get(model)
    if spec is None:
        raise ValueError(f"Unknown internal model '{model}'. Use --list, or pass --source/--model-path.")
    source_path = _resolve_output_file(root, spec["output"])
    data = json.loads(source_path.read_text(encoding="utf-8"))
    return {"model": {"name": model, "type": spec["type"]}, "source": str(source_path), "data": data}


def run_leaderboard(root: Path, output: Path) -> None:
    """Regenerate docs/leaderboard.md from stored internal + external results."""
    from benchmark.leaderboard import build_leaderboard_markdown

    markdown = build_leaderboard_markdown(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"[run.py] leaderboard written to {output}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="two_step", help="Model name (internal) or --model-path class")
    parser.add_argument("--city", default="nyc", choices=SUPPORTED_CITIES,
                        help="City context (currently only nyc has real data; others are stubs)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible runs")
    parser.add_argument("--source", type=Path, default=None,
                        help="Path to a precomputed result JSON to validate + record")
    parser.add_argument("--model-path", type=Path, default=None, help="Path to external model .py")
    parser.add_argument("--model-class", default=None, help="Class name in external model .py")
    parser.add_argument("--model-type", default=None, choices=["forecast", "policy", "rl_policy"],
                        help="External model type")
    parser.add_argument("--leaderboard", action="store_true",
                        help="Regenerate docs/leaderboard.md from stored results")
    parser.add_argument("--list", action="store_true", help="List supported internal models and cities")
    parser.add_argument("--output", type=Path, default=None,
                        help="Where to write the per-run result JSON (default: outputs/benchmark/<model>_<city>.json)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    root = ROOT

    if args.list:
        print("Internal models:")
        for name in sorted(INTERNAL_MODELS):
            print(f"  - {name:14s} type={INTERNAL_MODELS[name]['type']}")
        print(f"Cities: {', '.join(SUPPORTED_CITIES)}")
        return 0

    if args.leaderboard:
        output = args.output or root / "docs" / "leaderboard.md"
        run_leaderboard(root, output)
        return 0

    # 1) External source JSON (highest priority — direct validation)
    if args.source is not None:
        data = json.loads(args.source.read_text(encoding="utf-8"))
        errors = validate_result(data)
        if errors:
            print(f"[run.py] ERROR: {args.source} failed schema validation: {errors}", file=sys.stderr)
            return 1
        model = data.get("model", {}).get("name", args.source.stem)
        model_type = data.get("model", {}).get("type", "policy")
        result = {"model": {"name": model, "type": model_type}, "source": str(args.source), "data": data}

    # 2) External model class (reuses run_external_model.py)
    elif args.model_path is not None:
        from benchmark.runners.run_external_model import load_model_class, run_benchmark

        class_name = args.model_class or args.model.split("_")[-1].title()
        model_cls = load_model_class(str(args.model_path), class_name)
        model_type = args.model_type or _infer_external_type(model_cls)
        raw = run_benchmark(model_cls, model_type)
        errors = validate_result(raw)
        if errors:
            print(f"[run.py] ERROR: external model produced invalid result: {errors}", file=sys.stderr)
            return 1
        result = {"model": {"name": class_name, "type": model_type}, "source": str(args.model_path), "data": raw}

    # 3) Internal baseline (checked-in benchmark artifacts)
    else:
        if args.city not in SUPPORTED_CITIES:
            print(f"[run.py] ERROR: unsupported city '{args.city}'", file=sys.stderr)
            return 1
        result = load_source_result(root, args.model)

    # Stamp provenance — never fabricate metrics.
    record = {
        "run": {
            "model": result["model"]["name"],
            "type": result["model"]["type"],
            "city": args.city,
            "seed": args.seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": result["source"],
            "evaluation_type": "simulator/historical_replay",
        },
        "data": result["data"],
    }

    out_path = args.output or root / "outputs" / "benchmark" / f"{result['model']['name']}_{args.city}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    print(json.dumps({"model": record["run"]["model"], "city": args.city,
                      "source": record["run"]["source"], "saved_to": str(out_path)}, indent=2))
    print("[run.py] Evaluation type: SIMULATOR / HISTORICAL-REPLAY only. Not production evidence.")
    return 0


def _infer_external_type(model_cls) -> str:
    """Best-effort interface-based type inference for external models."""
    from src.interfaces import ForecastModel, Policy, RLPolicy

    if isinstance(model_cls, type):
        if issubclass(model_cls, RLPolicy):
            return "rl_policy"
        if issubclass(model_cls, Policy):
            return "policy"
        if issubclass(model_cls, ForecastModel):
            return "forecast"
    return "policy"


if __name__ == "__main__":
    sys.exit(main())

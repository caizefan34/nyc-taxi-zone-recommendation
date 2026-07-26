"""Unified experiment runner: reproduce any benchmark with a single command.

Usage:
    python scripts/run_experiment.py --config configs/model.yaml --benchmark rl
    python scripts/run_experiment.py --config configs/rl.yaml --benchmark ope
    python scripts/run_experiment.py --benchmark all

Records random seed, environment version, and model parameters in the output.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Warning: config not found: {p}")
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_config_value(cfg: dict, key: str, default=None):
    """Get a dot-notation key from nested dict."""
    keys = key.split(".")
    val = cfg
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, default)
        else:
            return default
    return val


def _record_metadata() -> dict:
    """Capture environment metadata for reproducibility."""
    import importlib

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "seed": _get_config_value(_load_yaml(str(ROOT / "configs/rl.yaml")), "rl.training.seed", 42),
    }

    # Capture package versions
    packages = ["numpy", "torch", "pandas", "scipy", "lightgbm", "xgboost", "gymnasium"]
    for pkg in packages:
        try:
            mod = importlib.import_module(pkg)
            metadata[f"{pkg}_version"] = getattr(mod, "__version__", "unknown")
        except ImportError:
            pass

    return metadata


def _run_rl_benchmark(config: dict, output_dir: Path) -> dict:
    """Run RL benchmark v2."""
    sys.path.insert(0, str(ROOT))
    from scripts.run_rl_benchmark_v2 import main as rl_benchmark_main

    # Setup args
    drivers = _get_config_value(config, "simulator.v2.driver_count", 50)
    seed = _get_config_value(config, "rl.training.seed", 42)
    output = output_dir / "rl_benchmark_v2.json"

    sys.argv = [
        "run_rl_benchmark_v2.py",
        "--drivers", str(drivers),
        "--seed", str(seed),
        "--output", str(output),
    ]
    rl_benchmark_main()
    return {"status": "completed", "output": str(output)}


def _run_forecast_benchmark(config: dict, output_dir: Path) -> dict:
    """Run forecasting benchmark."""
    sys.path.insert(0, str(ROOT))
    from scripts.run_forecast_benchmark import main as forecast_main

    output = output_dir / "forecasting_benchmark.json"
    sys.argv = [
        "run_forecast_benchmark.py",
        "--output", str(output),
    ]
    forecast_main()
    return {"status": "completed", "output": str(output)}


def _run_ope_comparison(config: dict, output_dir: Path) -> dict:
    """Run OPE comparison."""
    sys.path.insert(0, str(ROOT))
    from scripts.run_ope_comparison import main as ope_main

    drivers = _get_config_value(config, "rl.evaluation.drivers", 10)
    seed = _get_config_value(config, "rl.evaluation.seed", 42)
    output = output_dir / "policy_evaluation_report.md"

    sys.argv = [
        "run_ope_comparison.py",
        "--drivers", str(drivers),
        "--seed", str(seed),
        "--output", str(output),
    ]
    ope_main()
    return {"status": "completed", "output": str(output)}


def _run_benchmark_statistics(config: dict, output_dir: Path) -> dict:
    """Run benchmark statistics."""
    sys.path.insert(0, str(ROOT))
    from scripts.run_benchmark_statistics import main as stats_main

    output = output_dir / "benchmark_statistics.md"
    sys.argv = [
        "run_benchmark_statistics.py",
        "--output", str(output),
    ]
    stats_main()
    return {"status": "completed", "output": str(output)}


def main():
    parser = argparse.ArgumentParser(description="Unified experiment runner")
    parser.add_argument("--config", type=str, default="configs/config.yaml",
                       help="Path to main config file")
    parser.add_argument("--benchmark", type=str, choices=["rl", "forecast", "ope", "stats", "all"],
                       default="all", help="Which benchmark to run")
    parser.add_argument("--output", type=str, default=None,
                       help="Output directory (default: outputs/)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print what would be run without executing")
    args = parser.parse_args()

    # Load config
    config = _load_yaml(ROOT / args.config)
    config.update(_load_yaml(ROOT / "configs/rl.yaml"))
    config.update(_load_yaml(ROOT / "configs/simulator.yaml"))
    config.update(_load_yaml(ROOT / "configs/model.yaml"))

    # Setup output dir
    output_dir = Path(args.output) if args.output else ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create experiment record
    metadata = _record_metadata()
    manifest = {
        "experiment": {
            "command": " ".join(sys.argv),
            "date": metadata["timestamp"],
            "seed": metadata["seed"],
            "config_files": [args.config, "configs/rl.yaml", "configs/simulator.yaml", "configs/model.yaml"],
        },
        "versions": {k: v for k, v in metadata.items() if k.endswith("_version")},
        "benchmarks": {},
    }

    # Print plan
    benchmarks_to_run = []
    if args.benchmark in ("rl", "all"):
        benchmarks_to_run.append(("rl", "RL Benchmark v2", _run_rl_benchmark))
    if args.benchmark in ("forecast", "all"):
        benchmarks_to_run.append(("forecast", "Forecast Benchmark", _run_forecast_benchmark))
    if args.benchmark in ("ope", "all"):
        benchmarks_to_run.append(("ope", "OPE Comparison", _run_ope_comparison))
    if args.benchmark in ("stats", "all"):
        benchmarks_to_run.append(("stats", "Benchmark Statistics", _run_benchmark_statistics))

    print(f"{'='*60}")
    print("NYC Taxi Zone Recommendation - Experiment Runner")
    print(f"{'='*60}")
    print(f"Date: {metadata['timestamp']}")
    print(f"Config: {args.config}")
    print(f"Seed: {metadata['seed']}")
    print(f"Benchmark: {args.benchmark}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")
    print()

    if args.dry_run:
        print("Dry-run mode. Would execute:")
        for name, desc, _ in benchmarks_to_run:
            print(f"  - {desc}")
        return

    # Run benchmarks sequentially
    for name, desc, func in benchmarks_to_run:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running {desc}...")
        t0 = time.time()
        try:
            result = func(config, output_dir)
            elapsed = time.time() - t0
            manifest["benchmarks"][name] = {
                "status": result["status"],
                "output": result["output"],
                "elapsed_seconds": round(elapsed, 2),
            }
            print(f"  Completed in {elapsed:.1f}s -> {result['output']}")
        except Exception as e:
            elapsed = time.time() - t0
            manifest["benchmarks"][name] = {
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2),
            }
            print(f"  Failed after {elapsed:.1f}s: {e}")

    # Write experiment manifest
    manifest_path = output_dir / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nExperiment manifest: {manifest_path}")
    print("Done.")


if __name__ == "__main__":
    main()

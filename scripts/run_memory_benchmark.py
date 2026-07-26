"""Memory benchmark for recommendation strategies.

Uses tracemalloc to measure peak memory during inference.
Output: outputs/memory_benchmark.json + outputs/memory_benchmark.md
"""
from __future__ import annotations

import argparse
import json
import sys
import tracemalloc
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ZONE_COUNT = 263


def _measure_memory(strategy_fn, n_queries: int = 100) -> dict:
    """Measure peak memory for a strategy function."""
    rng = np.random.default_rng(42)

    tracemalloc.start()
    try:
        for _ in range(n_queries):
            t = datetime(2023, 1, rng.integers(25, 32), rng.integers(0, 24), rng.integers(0, 60))
            loc = int(rng.integers(1, ZONE_COUNT + 1))
            _ = strategy_fn(t, loc)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return {
        "peak_bytes": peak,
        "peak_mb": peak / (1024 * 1024),
        "n_queries": n_queries,
    }


def _stay_policy(t, loc):
    return (loc, loc, loc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/memory_benchmark.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/memory_benchmark.md")
    args = parser.parse_args()

    results = {}

    print("Measuring Stay policy memory...")
    results["stay"] = _measure_memory(_stay_policy, args.queries)

    lines = [
        "# Memory Benchmark",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        f"**Queries:** {args.queries}",
        "",
        "| Strategy | Peak Memory (MB) |",
        "|----------|-----------------:|",
    ]

    for name, data in results.items():
        lines.append(f"| {name} | {data['peak_mb']:.2f} |")

    report_md = "\n".join(lines)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(report_md, encoding="utf-8")

    print(json.dumps(results, indent=2))
    print(f"\nReport: {args.report}")


if __name__ == "__main__":
    main()

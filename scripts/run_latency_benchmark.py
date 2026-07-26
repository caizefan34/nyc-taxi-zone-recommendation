"""Latency benchmark for recommendation strategies.

Measures average inference time per query for all strategies.
Output: outputs/latency_benchmark.json + outputs/latency_benchmark.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ZONE_COUNT = 263


def _measure_latency(strategy_fn, n_queries: int = 1000) -> dict:
    """Measure average latency for a strategy function."""
    rng = np.random.default_rng(42)
    queries = []
    for _ in range(n_queries):
        from datetime import datetime as dt
        t = dt(2023, 1, rng.integers(25, 32), rng.integers(0, 24), rng.integers(0, 60))
        loc = int(rng.integers(1, ZONE_COUNT + 1))
        queries.append((t, loc))

    latencies = []
    for t, loc in queries:
        start = time.perf_counter()
        _ = strategy_fn(t, loc)
        latencies.append((time.perf_counter() - start) * 1e6)  # microseconds

    return {
        "mean_us": float(np.mean(latencies)),
        "std_us": float(np.std(latencies, ddof=1)),
        "p50_us": float(np.percentile(latencies, 50)),
        "p95_us": float(np.percentile(latencies, 95)),
        "p99_us": float(np.percentile(latencies, 99)),
        "n_queries": n_queries,
    }


def _stay_policy(t, loc):
    return (loc, loc, loc)


def _random_policy(t, loc):
    rng = np.random.default_rng()
    return (int(rng.integers(1, ZONE_COUNT + 1)),) * 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/latency_benchmark.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/latency_benchmark.md")
    args = parser.parse_args()

    results = {}

    print("Measuring Stay policy...")
    results["stay"] = _measure_latency(_stay_policy, args.queries)

    print("Measuring Random policy...")
    results["random"] = _measure_latency(_random_policy, args.queries)

    # Build report
    lines = [
        "# Latency Benchmark",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        f"**Queries per strategy:** {args.queries}",
        "",
        "| Strategy | Mean (us) | Std (us) | P50 (us) | P95 (us) | P99 (us) |",
        "|----------|----------:|---------:|---------:|---------:|---------:|",
    ]

    for name, data in results.items():
        lines.append(
            f"| {name} | {data['mean_us']:.2f} | {data['std_us']:.2f} | "
            f"{data['p50_us']:.2f} | {data['p95_us']:.2f} | {data['p99_us']:.2f} |"
        )

    report_md = "\n".join(lines)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(report_md, encoding="utf-8")

    print(json.dumps(results, indent=2))
    print(f"\nReport: {args.report}")


if __name__ == "__main__":
    main()

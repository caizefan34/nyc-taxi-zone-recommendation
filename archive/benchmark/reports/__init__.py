"""Benchmark report generation.

Generates standardized JSON reports for benchmark runs,
including metadata, results, and environment information.
"""

from __future__ import annotations

import json
import time
from typing import Any

from archive.benchmark import __version__


def generate_report(results: dict[str, dict[str, float]], benchmark_type: str) -> dict[str, Any]:
    """Generate a standardized benchmark report.
    
    Args:
        results: Dict mapping model names to their metric dicts.
        benchmark_type: One of 'forecast', 'decision', 'rl', 'robustness'.
    
    Returns:
        Dict with metadata and results.
    """
    return {
        "benchmark": benchmark_type,
        "version": __version__,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results,
    }


def save_report(report: dict[str, Any], path: str) -> None:
    """Save a benchmark report to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


__all__ = ["generate_report", "save_report"]

"""Exposure concentration and coverage metrics for ranked recommendations."""
from __future__ import annotations

import numpy as np


def gini(values) -> float:
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or np.any(values < 0.0):
        raise ValueError("values must be a non-negative vector")
    if len(values) == 0 or float(values.sum()) == 0.0:
        return 0.0
    ordered = np.sort(values)
    n = len(ordered)
    return float((2.0 * np.dot(np.arange(1, n + 1), ordered) / (n * ordered.sum())) - (n + 1) / n)


def exposure_metrics(rankings, *, zone_count: int = 263, weights=(0.6, 0.3, 0.1)) -> dict[str, object]:
    rankings = np.asarray(rankings, dtype=int)
    if rankings.ndim != 2 or rankings.shape[1] != len(weights):
        raise ValueError("rankings must have one column per rank weight")
    if np.any(rankings < 1) or np.any(rankings > zone_count):
        raise ValueError("zone IDs are out of range")
    exposure = np.zeros(zone_count, dtype=float)
    for rank, weight in enumerate(weights):
        np.add.at(exposure, rankings[:, rank] - 1, float(weight))
    shares = exposure / exposure.sum() if exposure.sum() else exposure
    positive = shares[shares > 0.0]
    entropy = float(-np.sum(positive * np.log(positive)))
    return {
        "unique_zones": int(np.count_nonzero(exposure)),
        "coverage": float(np.count_nonzero(exposure) / zone_count),
        "gini": gini(exposure),
        "top_1pct_share": float(np.sort(shares)[-max(1, round(zone_count * 0.01)):].sum()),
        "top_10pct_share": float(np.sort(shares)[-max(1, round(zone_count * 0.10)):].sum()),
        "entropy": entropy,
        "effective_zone_count": float(np.exp(entropy)),
        "exposure": exposure.tolist(),
    }


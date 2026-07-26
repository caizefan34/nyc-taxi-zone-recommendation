from __future__ import annotations

import pandas as pd
import pytest

from src.audit.counterfactual import doubly_robust, ips, snips
from src.audit.fairness import exposure_metrics, gini
from src.audit.statistics import paired_comparison
from src.audit.temporal import exact_trip_overlap, rolling_time_splits, validate_temporal_partition


def test_rolling_splits_are_strictly_temporal():
    splits = rolling_time_splits("2023-01-01", "2023-02-01", train_days=14, validation_days=7)
    assert len(splits) == 2
    assert all(split.train_end == split.validation_start for split in splits)
    assert all(split.validation_end <= pd.Timestamp("2023-02-01") for split in splits)


def test_partition_and_overlap_detection():
    result = validate_temporal_partition(["2023-01-01"], ["2023-01-24 23:59"], ["2023-01-25"], ["2023-01-25 00:30"])
    assert result["strictly_separated"]
    train = pd.DataFrame({"id": [1, 2], "fare": [10.0, 20.0]})
    validation = pd.DataFrame({"id": [2, 3], "fare": [20.0, 30.0]})
    assert exact_trip_overlap(train, validation, ["id", "fare"]) == 1


def test_counterfactual_estimators_on_uniform_logging():
    reward = [1.0, 0.0, 1.0, 0.0]
    target = [0.5] * 4
    behavior = [0.5] * 4
    assert ips(reward, target, behavior) == pytest.approx(0.5)
    assert snips(reward, target, behavior) == pytest.approx(0.5)
    assert doubly_robust(reward, target, behavior, [0.5] * 4, [0.5] * 4) == pytest.approx(0.5)


def test_counterfactual_estimators_require_logged_support():
    with pytest.raises(ValueError):
        ips([1.0], [1.0], [0.0])


def test_paired_statistics_and_fairness_metrics():
    comparison = paired_comparison([2, 3, 4, 5], [1, 2, 3, 4], bootstrap_samples=500)
    assert comparison["mean_difference"] == pytest.approx(1.0)
    assert comparison["ci95_low"] == pytest.approx(1.0)
    assert gini([1, 1, 1]) == pytest.approx(0.0)
    metrics = exposure_metrics([[1, 2, 3], [1, 2, 4]], zone_count=4)
    assert metrics["coverage"] == pytest.approx(1.0)
    assert metrics["gini"] > 0.0

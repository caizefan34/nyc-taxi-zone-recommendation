"""A/B Testing Framework for policy comparison.

Compares control and treatment policies with bootstrap confidence intervals,
effect size, and statistical significance. Clearly labels data source
(SIMULATION / HISTORICAL REPLAY / SHADOW / REAL A/B).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class ExperimentSource(str, Enum):
    SIMULATION = "simulation"
    HISTORICAL_REPLAY = "historical_replay"
    SHADOW = "shadow"
    REAL_AB = "real_ab"


@dataclass
class PolicyMetrics:
    """Metrics for one policy evaluation run."""

    policy_name: str
    revenue_per_vehicle: list[float] = field(default_factory=list)
    utilization: list[float] = field(default_factory=list)
    empty_distance: list[float] = field(default_factory=list)
    wait_time: list[float] = field(default_factory=list)
    trip_completion: list[float] = field(default_factory=list)
    recommendation_acceptance: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {"policy_name": self.policy_name}
        for key in (
            "revenue_per_vehicle", "utilization", "empty_distance",
            "wait_time", "trip_completion", "recommendation_acceptance",
        ):
            vals = getattr(self, key)
            if vals:
                result[f"{key}_mean"] = round(float(np.mean(vals)), 4)
                result[f"{key}_std"] = round(float(np.std(vals)), 4)
        return result


@dataclass
class ABResult:
    """Result of A/B comparison between two policies."""

    control_name: str
    treatment_name: str
    source: ExperimentSource
    n_bootstrap: int

    # Per-metric comparisons
    metric_results: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "control": self.control_name,
            "treatment": self.treatment_name,
            "source": self.source.value,
            "n_bootstrap": self.n_bootstrap,
            "metrics": self.metric_results,
            "note": self._source_note(),
        }

    def _source_note(self) -> str:
        notes = {
            ExperimentSource.SIMULATION: "Results from simulator. Not production evidence.",
            ExperimentSource.HISTORICAL_REPLAY: "Results from historical replay. Not production evidence.",
            ExperimentSource.SHADOW: "Shadow evaluation. Recommendations recorded but not executed.",
            ExperimentSource.REAL_AB: "Real-world A/B test results.",
        }
        return notes.get(self.source, "Unknown source")


def bootstrap_ci(
    values: list[float],
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap confidence interval for the mean."""
    rng = np.random.RandomState(seed)
    arr = np.asarray(values, dtype=float)
    means = []
    for _ in range(n_bootstrap):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(float(np.mean(sample)))
    means.sort()
    alpha = (1.0 - ci_level) / 2.0
    lo = means[int(alpha * n_bootstrap)]
    hi = means[int((1.0 - alpha) * n_bootstrap)]
    return lo, hi


def paired_comparison(
    control_values: list[float],
    treatment_values: list[float],
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict:
    """Paired bootstrap comparison of two sets of values.

    Returns:
        dict with mean_diff, ci_lower, ci_upper, effect_size (Cohen's d), significant
    """
    rng = np.random.RandomState(seed)
    ctrl = np.asarray(control_values, dtype=float)
    trt = np.asarray(treatment_values, dtype=float)
    diffs = trt - ctrl

    obs_diff = float(np.mean(diffs))

    boot_diffs = []
    n = len(diffs)
    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        boot_diffs.append(float(np.mean(diffs[idx])))
    boot_diffs.sort()

    alpha = 0.025
    ci_lower = boot_diffs[int(alpha * n_bootstrap)]
    ci_upper = boot_diffs[int((1.0 - alpha) * n_bootstrap)]

    # Cohen's d
    pooled_std = np.sqrt((np.var(ctrl) + np.var(trt)) / 2.0)
    effect_size = float(obs_diff / pooled_std) if pooled_std > 0 else 0.0

    significant = ci_lower > 0 or ci_upper < 0

    return {
        "mean_difference": round(obs_diff, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "effect_size_cohens_d": round(effect_size, 4),
        "statistically_significant": significant,
        "n_pairs": n,
    }


def compare_policies(
    control: PolicyMetrics,
    treatment: PolicyMetrics,
    source: ExperimentSource = ExperimentSource.SIMULATION,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> ABResult:
    """Run A/B comparison across all shared metrics."""
    result = ABResult(
        control_name=control.policy_name,
        treatment_name=treatment.policy_name,
        source=source,
        n_bootstrap=n_bootstrap,
    )

    metric_names = [
        "revenue_per_vehicle", "utilization", "empty_distance",
        "wait_time", "trip_completion", "recommendation_acceptance",
    ]

    for metric in metric_names:
        ctrl_vals = getattr(control, metric, [])
        trt_vals = getattr(treatment, metric, [])
        if ctrl_vals and trt_vals and len(ctrl_vals) == len(trt_vals):
            result.metric_results[metric] = paired_comparison(
                ctrl_vals, trt_vals, n_bootstrap=n_bootstrap, seed=seed,
            )

    return result


def generate_ab_report(
    result: ABResult,
    output_dir: str | Path = "outputs/ab",
) -> Path:
    """Save A/B test report to disk."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"ab_{result.control_name}_vs_{result.treatment_name}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2, default=str))
    logger.info("A/B report saved to %s", path)
    return path

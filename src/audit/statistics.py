"""Paired statistical inference helpers for strategy comparisons."""
from __future__ import annotations

import numpy as np
from scipy import stats


def paired_comparison(a, b, *, bootstrap_samples: int = 10_000, seed: int = 20230722) -> dict[str, float]:
    """Compare paired outcomes as a-b with CI, tests, and Cohen's dz."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or len(a) < 2:
        raise ValueError("paired inputs must be equal-length vectors with at least two observations")
    difference = a - b
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(difference), size=(bootstrap_samples, len(difference)))
    bootstrap_means = difference[indices].mean(axis=1)
    t_result = stats.ttest_rel(a, b)
    try:
        wilcoxon = stats.wilcoxon(a, b, zero_method="wilcox")
        wilcoxon_statistic = float(wilcoxon.statistic)
        wilcoxon_pvalue = float(wilcoxon.pvalue)
    except ValueError:
        wilcoxon_statistic = 0.0
        wilcoxon_pvalue = 1.0
    std = float(np.std(difference, ddof=1))
    return {
        "mean_a": float(np.mean(a)),
        "mean_b": float(np.mean(b)),
        "mean_difference": float(np.mean(difference)),
        "std_difference": std,
        "ci95_low": float(np.quantile(bootstrap_means, 0.025)),
        "ci95_high": float(np.quantile(bootstrap_means, 0.975)),
        "paired_t_statistic": float(t_result.statistic),
        "paired_t_pvalue": float(t_result.pvalue),
        "wilcoxon_statistic": wilcoxon_statistic,
        "wilcoxon_pvalue": wilcoxon_pvalue,
        "cohen_dz": float(np.mean(difference) / std) if std > 0.0 else 0.0,
    }


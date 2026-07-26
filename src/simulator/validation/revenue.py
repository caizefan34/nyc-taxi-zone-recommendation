"""Revenue validation: compare simulated driver rewards against real TLC fare data.

Compares:
- fare/reward distribution statistics
- per-zone average fare alignment
- total revenue distribution
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as scipy_stats


@dataclass
class RevenueValidationResult:
    """Revenue/fare distribution comparison results."""
    real_mean: float
    sim_mean: float
    real_median: float
    sim_median: float
    real_std: float
    sim_std: float
    mean_abs_error: float
    rmse: float
    correlation: float
    ks_statistic: float
    ks_pvalue: float
    n_real: int
    n_sim: int
    interpretation: str = ""


class RevenueValidator:
    """Validate revenue/fare distributions between simulator and real data."""

    def validate(
        self,
        real_fares: np.ndarray,
        sim_rewards: np.ndarray,
    ) -> RevenueValidationResult:
        """Compare real fare distribution with simulated driver reward distribution.

        Args:
            real_fares: Array of real TLC fare amounts.
            sim_rewards: Array of simulated driver rewards.

        Returns:
            RevenueValidationResult with all comparison metrics.
        """
        real_f = np.asarray(real_fares, dtype=np.float64).ravel()
        sim_f = np.asarray(sim_rewards, dtype=np.float64).ravel()

        real_mean = float(real_f.mean())
        sim_mean = float(sim_f.mean())
        real_median = float(np.median(real_f))
        sim_median = float(np.median(sim_f))
        real_std = float(real_f.std(ddof=1))
        sim_std = float(sim_f.std(ddof=1))

        # Mean absolute error between distributions (bin-wise)
        mae = float(np.abs(real_mean - sim_mean))

        # RMSE between distributions
        rmse = float(np.sqrt((real_mean - sim_mean) ** 2 + (real_std - sim_std) ** 2))

        # Correlation (requires same length, so we compare binned histograms)
        n_bins = min(50, max(10, min(len(real_f), len(sim_f)) // 10))
        real_hist, bin_edges = np.histogram(real_f, bins=n_bins, density=True)
        sim_hist, _ = np.histogram(sim_f, bins=bin_edges, density=True)
        corr = float(np.corrcoef(real_hist, sim_hist)[0, 1]) if len(real_hist) > 1 else 0.0

        # Two-sample KS test
        ks_stat, ks_pval = scipy_stats.ks_2samp(real_f, sim_f)

        # Interpretation
        diff_pct = abs(real_mean - sim_mean) / max(1e-6, abs(real_mean)) * 100
        if diff_pct < 5 and ks_pval > 0.05:
            interpretation = "Strong: Revenue distributions are statistically similar"
        elif diff_pct < 15 and ks_pval > 0.01:
            interpretation = "Moderate: Revenue distributions show acceptable alignment"
        elif diff_pct < 30:
            interpretation = "Weak: Revenue distributions differ notably"
        else:
            interpretation = "Poor: Revenue distributions are significantly different"

        return RevenueValidationResult(
            real_mean=real_mean,
            sim_mean=sim_mean,
            real_median=real_median,
            sim_median=sim_median,
            real_std=real_std,
            sim_std=sim_std,
            mean_abs_error=mae,
            rmse=rmse,
            correlation=corr,
            ks_statistic=float(ks_stat),
            ks_pvalue=float(ks_pval),
            n_real=int(len(real_f)),
            n_sim=int(len(sim_f)),
            interpretation=interpretation,
        )

    def validate_per_zone(
        self,
        real_zone_fares: dict[int, np.ndarray],
        sim_zone_rewards: dict[int, np.ndarray],
    ) -> dict[int, RevenueValidationResult]:
        """Compare fare/reward distributions per taxi zone.

        Args:
            real_zone_fares: Dict mapping zone_id to array of real fares.
            sim_zone_rewards: Dict mapping zone_id to array of simulated rewards.

        Returns:
            Dict mapping zone_id to RevenueValidationResult.
        """
        results: dict[int, RevenueValidationResult] = {}
        all_zones = set(real_zone_fares) | set(sim_zone_rewards)
        for zone in sorted(all_zones):
            real = real_zone_fares.get(zone, np.array([0.0]))
            sim = sim_zone_rewards.get(zone, np.array([0.0]))
            results[zone] = self.validate(real, sim)
        return results

"""Distribution comparison between simulator and real NYC TLC data.

Measures:
- KL divergence (zone demand distribution)
- Jensen-Shannon divergence
- Wasserstein distance (Earth Mover's Distance)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance


@dataclass
class DistributionMetrics:
    """Statistical distance metrics between two distributions."""
    kl_divergence: float
    js_divergence: float
    wasserstein_distance: float
    real_mean: float
    sim_mean: float
    real_std: float
    sim_std: float
    correlation: float
    sample_size: int


@dataclass
class ValidationReport:
    """Complete simulator validation report."""
    zone_demand: DistributionMetrics | None = None
    hourly_pattern: DistributionMetrics | None = None
    weekday_weekend: DistributionMetrics | None = None
    revenue: DistributionMetrics | None = None
    summary: dict[str, str] = field(default_factory=dict)


def _to_pmf(arr: np.ndarray, n_bins: int = 50):
    if arr.min() == arr.max():
        bins = np.linspace(arr.min() - 1, arr.max() + 1, n_bins + 1)
    else:
        bins = np.linspace(arr.min(), arr.max(), n_bins + 1)
    hist, _ = np.histogram(arr, bins=bins, density=True)
    pmf = hist / (hist.sum() + 1e-12)
    return pmf

def _safe_kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    eps = 1e-12
    p_pmf = _to_pmf(p)
    q_pmf = _to_pmf(q)
    n = min(len(p_pmf), len(q_pmf))
    p_smooth = (p_pmf[:n] + eps) / (p_pmf[:n].sum() + eps * n)
    q_smooth = (q_pmf[:n] + eps) / (q_pmf[:n].sum() + eps * n)
    mask = p_smooth > 0
    return 0.0 if not mask.any() else float(np.sum(p_smooth[mask] * np.log(p_smooth[mask] / q_smooth[mask])))

def _safe_js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    p_pmf = _to_pmf(p)
    q_pmf = _to_pmf(q)
    n = min(len(p_pmf), len(q_pmf))
    return float(jensenshannon(p_pmf[:n], q_pmf[:n]) ** 2)






def _safe_wasserstein(p: np.ndarray, q: np.ndarray) -> float:
    """Compute Wasserstein distance (1D Earth Mover's Distance)."""
    return float(wasserstein_distance(p, q))


def compare_distributions(
    real: np.ndarray,
    simulated: np.ndarray,
) -> DistributionMetrics:
    """Compare two demand/reward distributions using multiple metrics.

    Args:
        real: Real data array (e.g., zone pickup counts).
        simulated: Simulated data array (same shape).

    Returns:
        DistributionMetrics with all comparison metrics.
    """
    real_f = real.ravel().astype(np.float64)
    sim_f = simulated.ravel().astype(np.float64)

    return DistributionMetrics(
        kl_divergence=_safe_kl_divergence(real_f, sim_f),
        js_divergence=_safe_js_divergence(real_f, sim_f),
        wasserstein_distance=_safe_wasserstein(real_f, sim_f),
        real_mean=float(real_f.mean()),
        sim_mean=float(sim_f.mean()),
        real_std=float(real_f.std(ddof=1)),
        sim_std=float(sim_f.std(ddof=1)),
        correlation=float(np.corrcoef(real_f, sim_f)[0, 1]) if len(real_f) > 1 and len(real_f) == len(sim_f) else 0.0,
        sample_size=int(min(len(real_f), len(sim_f))),
    )


class SimulatorValidator:
    """Validate simulator output against real NYC TLC data.

    Usage:
        validator = SimulatorValidator()
        report = validator.run(real_demand, sim_demand, real_fares, sim_fares)
    """

    def run(
        self,
        real_zone_demand: np.ndarray,
        sim_zone_demand: np.ndarray,
        real_hourly: np.ndarray,
        sim_hourly: np.ndarray,
        real_fares: np.ndarray,
        sim_rewards: np.ndarray,
    ) -> ValidationReport:
        """Run all validation checks.

        Args:
            real_zone_demand: (n_zones,) real pickup distribution.
            sim_zone_demand: (n_zones,) simulated demand distribution.
            real_hourly: (24,) real hourly demand pattern.
            sim_hourly: (24,) simulated hourly demand pattern.
            real_fares: (n_samples,) real fare amounts.
            sim_rewards: (n_samples,) simulated driver rewards.

        Returns:
            ValidationReport with all metrics.
        """
        report = ValidationReport()

        # Zone demand distribution
        report.zone_demand = compare_distributions(real_zone_demand, sim_zone_demand)

        # Hourly pattern
        report.hourly_pattern = compare_distributions(real_hourly, sim_hourly)

        # Revenue/fare distribution
        if len(real_fares) > 0 and len(sim_rewards) > 0:
            report.revenue = compare_distributions(real_fares, sim_rewards)

        # Generate summary
        report.summary = self._generate_summary(report)
        return report

    def _generate_summary(self, report: ValidationReport) -> dict[str, str]:
        """Generate human-readable interpretation of validation results."""
        summary: dict[str, str] = {}

        if report.zone_demand:
            zd = report.zone_demand
            if zd.kl_divergence < 0.1:
                verdict = "Excellent match"
            elif zd.kl_divergence < 0.5:
                verdict = "Good match"
            elif zd.kl_divergence < 1.0:
                verdict = "Moderate match"
            else:
                verdict = "Poor match"
            summary["zone_demand"] = (
                f"{verdict} (KL={zd.kl_divergence:.4f}, JS={zd.js_divergence:.4f}, "
                f"Wasserstein={zd.wasserstein_distance:.2f}, "
                f"correlation={zd.correlation:.4f})"
            )

        if report.hourly_pattern:
            hp = report.hourly_pattern
            if hp.correlation > 0.9:
                verdict = "Strong temporal alignment"
            elif hp.correlation > 0.7:
                verdict = "Good temporal alignment"
            else:
                verdict = "Weak temporal alignment"
            summary["hourly_pattern"] = (
                f"{verdict} (correlation={hp.correlation:.4f}, "
                f"RMSE={np.sqrt((hp.real_mean - hp.sim_mean) ** 2):.4f})"
            )

        if report.revenue:
            rv = report.revenue
            diff_pct = abs(rv.real_mean - rv.sim_mean) / max(1e-6, rv.real_mean) * 100
            if diff_pct < 5:
                verdict = "Excellent revenue match"
            elif diff_pct < 15:
                verdict = "Good revenue match"
            elif diff_pct < 30:
                verdict = "Moderate revenue match"
            else:
                verdict = "Poor revenue match"
            summary["revenue"] = (
                f"{verdict} (real={rv.real_mean:.2f}, sim={rv.sim_mean:.2f}, "
                f"diff={diff_pct:.1f}%)"
            )

        return summary



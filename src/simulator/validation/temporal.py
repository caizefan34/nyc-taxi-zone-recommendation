"""Temporal pattern validation: compare simulated vs real hourly/weekly/seasonal patterns.

Metrics:
- RMSE between real and simulated hourly demand curves
- Pearson correlation for weekday/weekend patterns
- Seasonal pattern comparison
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class TemporalValidationResult:
    """Results of temporal pattern validation."""
    hourly_rmse: float
    hourly_correlation: float
    weekday_rmse: float
    weekday_correlation: float
    weekend_rmse: float
    weekend_correlation: float
    peak_hour_real: int
    peak_hour_sim: int
    trough_hour_real: int
    trough_hour_sim: int
    seasonality_rmse: float | None = None
    seasonality_correlation: float | None = None
    interpretation: dict[str, str] = field(default_factory=dict)


class TemporalValidator:
    """Validate temporal patterns between simulator and real data."""

    def validate_hourly(
        self,
        real_hourly: np.ndarray,
        sim_hourly: np.ndarray,
    ) -> dict[str, float]:
        """Compare hourly demand curves.

        Args:
            real_hourly: (24,) array of real mean demand by hour.
            sim_hourly: (24,) array of simulated mean demand by hour.

        Returns:
            Dict with rmse, correlation, peak/trough hours.
        """
        real_h = np.asarray(real_hourly, dtype=np.float64).ravel()
        sim_h = np.asarray(sim_hourly, dtype=np.float64).ravel()
        if len(real_h) != 24 or len(sim_h) != 24:
            raise ValueError("Hourly arrays must have length 24")

        rmse = float(np.sqrt(np.mean((real_h - sim_h) ** 2)))
        # Handle zero std case
        real_std = real_h.std(ddof=1)
        sim_std = sim_h.std(ddof=1)
        if real_std == 0 or sim_std == 0:
            corr = 0.0
        else:
            corr = float(np.corrcoef(real_h, sim_h)[0, 1])

        return {
            "rmse": rmse,
            "correlation": corr,
            "peak_hour_real": int(real_h.argmax()),
            "peak_hour_sim": int(sim_h.argmax()),
            "trough_hour_real": int(real_h.argmin()),
            "trough_hour_sim": int(sim_h.argmin()),
        }

    def validate_weekday_weekend(
        self,
        real_weekday: np.ndarray,
        sim_weekday: np.ndarray,
        real_weekend: np.ndarray,
        sim_weekend: np.ndarray,
    ) -> dict[str, float]:
        """Compare weekday and weekend patterns separately.

        Args:
            real_weekday: (24,) mean demand by hour on weekdays.
            sim_weekday: (24,) simulated demand by hour on weekdays.
            real_weekend: (24,) mean demand by hour on weekends.
            sim_weekend: (24,) simulated demand by hour on weekends.

        Returns:
            Dict with rmse and correlation for each.
        """
        r_wd = np.asarray(real_weekday, dtype=np.float64).ravel()
        s_wd = np.asarray(sim_weekday, dtype=np.float64).ravel()
        r_we = np.asarray(real_weekend, dtype=np.float64).ravel()
        s_we = np.asarray(sim_weekend, dtype=np.float64).ravel()

        wd_rmse = float(np.sqrt(np.mean((r_wd - s_wd) ** 2)))
        we_rmse = float(np.sqrt(np.mean((r_we - s_we) ** 2)))

        wd_corr = float(np.corrcoef(r_wd, s_wd)[0, 1]) if r_wd.std() > 0 and s_wd.std() > 0 else 0.0
        we_corr = float(np.corrcoef(r_we, s_we)[0, 1]) if r_we.std() > 0 and s_we.std() > 0 else 0.0

        return {
            "weekday_rmse": wd_rmse,
            "weekday_correlation": wd_corr,
            "weekend_rmse": we_rmse,
            "weekend_correlation": we_corr,
        }

    def validate_seasonality(
        self,
        real_monthly: np.ndarray,
        sim_monthly: np.ndarray,
    ) -> dict[str, float]:
        """Compare seasonal (monthly) demand patterns.

        Args:
            real_monthly: (12,) array of real mean demand by month.
            sim_monthly: (12,) array of simulated mean demand by month.

        Returns:
            Dict with rmse and correlation.
        """
        r_m = np.asarray(real_monthly, dtype=np.float64).ravel()
        s_m = np.asarray(sim_monthly, dtype=np.float64).ravel()

        rmse = float(np.sqrt(np.mean((r_m - s_m) ** 2)))
        corr = float(np.corrcoef(r_m, s_m)[0, 1]) if r_m.std() > 0 and s_m.std() > 0 else 0.0

        return {"seasonality_rmse": rmse, "seasonality_correlation": corr}

    def full_validation(
        self,
        real_by_hour: np.ndarray,
        sim_by_hour: np.ndarray,
        real_weekday: np.ndarray,
        sim_weekday: np.ndarray,
        real_weekend: np.ndarray,
        sim_weekend: np.ndarray,
        real_monthly: np.ndarray | None = None,
        sim_monthly: np.ndarray | None = None,
    ) -> TemporalValidationResult:
        """Run all temporal validations and return a comprehensive result.

        Args:
            real_by_hour: (24,) real mean demand by hour.
            sim_by_hour: (24,) simulated mean demand by hour.
            real_weekday: (24,) real weekday demand by hour.
            sim_weekday: (24,) simulated weekday demand by hour.
            real_weekend: (24,) real weekend demand by hour.
            sim_weekend: (24,) simulated weekend demand by hour.
            real_monthly: (12,) optional real monthly demand.
            sim_monthly: (12,) optional simulated monthly demand.

        Returns:
            TemporalValidationResult with all computed metrics.
        """
        hourly = self.validate_hourly(real_by_hour, sim_by_hour)
        wd_we = self.validate_weekday_weekend(
            real_weekday, sim_weekday, real_weekend, sim_weekend
        )

        seasonality = None
        if real_monthly is not None and sim_monthly is not None:
            seasonality = self.validate_seasonality(real_monthly, sim_monthly)

        result = TemporalValidationResult(
            hourly_rmse=hourly["rmse"],
            hourly_correlation=hourly["correlation"],
            weekday_rmse=wd_we["weekday_rmse"],
            weekday_correlation=wd_we["weekday_correlation"],
            weekend_rmse=wd_we["weekend_rmse"],
            weekend_correlation=wd_we["weekend_correlation"],
            peak_hour_real=hourly["peak_hour_real"],
            peak_hour_sim=hourly["peak_hour_sim"],
            trough_hour_real=hourly["trough_hour_real"],
            trough_hour_sim=hourly["trough_hour_sim"],
            seasonality_rmse=seasonality["seasonality_rmse"] if seasonality else None,
            seasonality_correlation=seasonality["seasonality_correlation"] if seasonality else None,
        )

        # Generate interpretation
        result.interpretation = {
            "hourly": (
                f"Hourly correlation: {hourly['correlation']:.4f} "
                f"(RMSE={hourly['rmse']:.2f})"
            ),
            "weekday": (
                f"Weekday correlation: {wd_we['weekday_correlation']:.4f} "
                f"(RMSE={wd_we['weekday_rmse']:.2f})"
            ),
            "weekend": (
                f"Weekend correlation: {wd_we['weekend_correlation']:.4f} "
                f"(RMSE={wd_we['weekend_rmse']:.2f})"
            ),
        }
        if seasonality:
            result.interpretation["seasonality"] = (
                f"Seasonality correlation: {seasonality['seasonality_correlation']:.4f} "
                f"(RMSE={seasonality['seasonality_rmse']:.2f})"
            )

        return result

"""Unified interface for external urban feature providers.

All feature providers must:
- Implement ``ExternalFeatureProvider``
- Return ``FeatureCollection`` with timestamp-aligned arrays
- Support configurable time ranges (2022–2025)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureCollection:
    """Timestamp-aligned collection of external features.

    All array attributes share the same first dimension (``n_timestamps``).
    """

    timestamps: pd.DatetimeIndex
    """Sorted, unique, evenly-spaced half-hour timestamps."""

    data: dict[str, np.ndarray]
    """Feature name → 1-D or 2-D array indexed by timestamps."""

    def __post_init__(self) -> None:
        if not isinstance(self.timestamps, pd.DatetimeIndex):
            raise TypeError("timestamps must be a DatetimeIndex")
        if not self.timestamps.is_monotonic_increasing:
            raise ValueError("timestamps must be monotonically increasing")
        n = len(self.timestamps)
        for name, arr in self.data.items():
            if not isinstance(arr, np.ndarray):
                raise TypeError(f"feature '{name}' must be a numpy array")
            if arr.shape[0] != n:
                raise ValueError(
                    f"feature '{name}' has {arr.shape[0]} rows, expected {n}"
                )

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(self.data.keys())

    @property
    def n_timestamps(self) -> int:
        return len(self.timestamps)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to a flat DataFrame with a ``timestamp`` column."""
        df = pd.DataFrame({"timestamp": self.timestamps})
        for name, arr in self.data.items():
            if arr.ndim == 1:
                df[name] = arr
            else:
                for col_idx in range(arr.shape[1]):
                    df[f"{name}_{col_idx}"] = arr[:, col_idx]
        return df


class ExternalFeatureProvider(ABC):
    """Abstract base for all external feature providers.

    Subclasses must implement ``get_features(start, end)`` which returns
    half-hourly features for the queried time range.
    """

    @abstractmethod
    def get_features(
        self,
        start: str | datetime | pd.Timestamp,
        end: str | datetime | pd.Timestamp,
    ) -> FeatureCollection:
        """Return timestamp-aligned features for the half-hourly grid in [start, end).

        Args:
            start: Inclusive start of the query window.
            end: Exclusive end of the query window.

        Returns:
            ``FeatureCollection`` with half-hourly timestamps.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. ``"weather"``, ``"calendar"``)."""
        ...

    @staticmethod
    def _half_hour_grid(
        start: str | datetime | pd.Timestamp,
        end: str | datetime | pd.Timestamp,
    ) -> pd.DatetimeIndex:
        """Build a half-hourly datetime index covering [start, end)."""
        start_ts = pd.Timestamp(start).ceil("30min")
        end_ts = pd.Timestamp(end).floor("30min")
        if start_ts >= end_ts:
            raise ValueError(
                f"start ({start_ts}) must be before end ({end_ts})"
            )
        return pd.date_range(start_ts, end_ts, freq="30min", inclusive="left")


def align_features(
    target_timestamps: pd.DatetimeIndex,
    *providers: ExternalFeatureProvider,
) -> pd.DataFrame:
    """Collect and align features from multiple providers to common timestamps.

    Args:
        target_timestamps: Target half-hour grid.
        *providers: Feature providers to query.

    Returns:
        DataFrame with a ``timestamp`` column and provider feature columns.
    """
    periods = len(target_timestamps)
    combined: dict[str, np.ndarray] = {"timestamp": np.asarray(target_timestamps)}

    for provider in providers:
        if periods == 0:
            continue
        start = target_timestamps[0]
        end = target_timestamps[-1] + pd.Timedelta(minutes=30)
        collection = provider.get_features(start, end)

        for name, arr in collection.data.items():
            col_name = f"{provider.name}_{name}"
            # Handle multi-dimensional arrays by flattening or selecting first dim
            if arr.ndim == 1:
                reindexed = np.interp(
                    target_timestamps.asi8,
                    collection.timestamps.asi8,
                    arr
                )
                combined[col_name] = reindexed
            else:
                for d in range(arr.shape[1]):
                    sub_name = f"{col_name}_{d}"
                    reindexed = np.interp(
                        target_timestamps.asi8,
                        collection.timestamps.asi8,
                        arr[:, d]
                    )
                    combined[sub_name] = reindexed

    return pd.DataFrame(combined)

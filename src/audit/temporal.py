"""Temporal split and leakage checks for trip-level experiments."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class TemporalSplit:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp


def rolling_time_splits(
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    *,
    train_days: int,
    validation_days: int,
    step_days: int | None = None,
) -> list[TemporalSplit]:
    """Create expanding-window train/validation splits with strict chronology."""
    if train_days <= 0 or validation_days <= 0:
        raise ValueError("train_days and validation_days must be positive")
    step_days = validation_days if step_days is None else step_days
    if step_days <= 0:
        raise ValueError("step_days must be positive")

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    train_end = start_ts + timedelta(days=train_days)
    splits: list[TemporalSplit] = []
    while train_end + timedelta(days=validation_days) <= end_ts:
        validation_end = train_end + timedelta(days=validation_days)
        splits.append(TemporalSplit(start_ts, train_end, train_end, validation_end))
        train_end += timedelta(days=step_days)
    return splits


def validate_temporal_partition(
    train_pickups: Iterable[object],
    train_dropoffs: Iterable[object],
    validation_pickups: Iterable[object],
    validation_dropoffs: Iterable[object],
) -> dict[str, object]:
    """Verify that all training trips finish before validation begins."""
    train_pu = pd.to_datetime(pd.Series(train_pickups), errors="coerce")
    train_do = pd.to_datetime(pd.Series(train_dropoffs), errors="coerce")
    val_pu = pd.to_datetime(pd.Series(validation_pickups), errors="coerce")
    val_do = pd.to_datetime(pd.Series(validation_dropoffs), errors="coerce")
    if any(series.isna().any() for series in (train_pu, train_do, val_pu, val_do)):
        raise ValueError("timestamps must be valid datetimes")
    train_end = max(train_pu.max(), train_do.max())
    validation_start = min(val_pu.min(), val_do.min())
    return {
        "train_end": train_end,
        "validation_start": validation_start,
        "strictly_separated": bool(train_end < validation_start),
        "boundary_separated": bool(train_end <= validation_start),
    }


def exact_trip_overlap(train: pd.DataFrame, validation: pd.DataFrame, columns: list[str]) -> int:
    """Count exact cross-split duplicate trip keys."""
    missing = [column for column in columns if column not in train or column not in validation]
    if missing:
        raise ValueError(f"missing overlap columns: {missing}")
    train_keys = train[columns].drop_duplicates()
    validation_keys = validation[columns].drop_duplicates()
    return int(train_keys.merge(validation_keys, on=columns, how="inner").shape[0])


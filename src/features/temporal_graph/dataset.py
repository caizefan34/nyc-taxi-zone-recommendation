"""Dataset and collator for temporal graph forecasting.

Prepares sliding-window sequences from historical demand data
with optional external features.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class TemporalGraphDataset(Dataset):
    """Sliding-window dataset for temporal graph forecasting.

    Each sample is a sequence of ``history_steps`` half-hour observations
    used to predict the next ``forecast_steps`` half-hour observations.

    Args:
        demand: ``(n_timestamps, zone_count)`` demand array.
        history_steps: Number of past steps to use as input.
        forecast_steps: Number of future steps to predict.
        timestamps: Optional ``DatetimeIndex`` for time alignment.
        external_features: Optional ``(n_timestamps, zone_count, feat_dim)`` or
            ``(n_timestamps, feat_dim)`` external features.
    """

    def __init__(
        self,
        demand: np.ndarray,
        *,
        history_steps: int = 48,
        forecast_steps: int = 48,
        timestamps: pd.DatetimeIndex | None = None,
        external_features: np.ndarray | None = None,
    ) -> None:
        if demand.ndim != 2:
            raise ValueError(f"demand must be 2-D (time, zones), got shape {demand.shape}")
        if demand.shape[0] < history_steps + forecast_steps:
            raise ValueError(
                f"demand has {demand.shape[0]} timestamps, need at least "
                f"{history_steps + forecast_steps}"
            )

        self.demand = np.asarray(demand, dtype=np.float32)
        self.history_steps = history_steps
        self.forecast_steps = forecast_steps
        self.zone_count = demand.shape[1]
        self.timestamps = timestamps
        self.external_features = None

        if external_features is not None:
            ext = np.asarray(external_features, dtype=np.float32)
            if ext.ndim == 2:
                # (time, feat) → broadcast to zones
                ext = ext[:, np.newaxis, :]
            if ext.shape[0] != demand.shape[0]:
                raise ValueError(
                    f"external_features timestamps ({ext.shape[0]}) "
                    f"don't match demand ({demand.shape[0]})"
                )
            self.external_features = ext

    def __len__(self) -> int:
        return self.demand.shape[0] - self.history_steps - self.forecast_steps + 1

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        start = index
        mid = index + self.history_steps
        end = index + self.history_steps + self.forecast_steps

        history = self.demand[start:mid]  # (history, zones)
        targets = self.demand[mid:end]   # (forecast, zones)

        item: dict[str, torch.Tensor] = {
            "demand_history": torch.as_tensor(history),
            "targets": torch.as_tensor(targets),
        }

        if self.external_features is not None:
            ext_history = self.external_features[start:mid]
            item["external_features"] = torch.as_tensor(ext_history)

        if self.timestamps is not None:
            item["start_time"] = torch.as_tensor(
                self.timestamps[mid].value, dtype=torch.int64
            )

        return item


def collate_sequences(
    batch: list[dict[str, torch.Tensor]],
) -> dict[str, torch.Tensor]:
    """Collate a list of samples into batched tensors.

    Args:
        batch: List of dicts from ``TemporalGraphDataset.__getitem__``.

    Returns:
        Batched dict with keys ``"demand_history"``, ``"targets"``,
        and optionally ``"external_features"``.
    """
    result: dict[str, torch.Tensor] = {}
    for key in batch[0]:
        result[key] = torch.stack([b[key] for b in batch], dim=0)
    return result

"""Composite provider that merges multiple ExternalFeatureProviders.

All features are aligned to a common half-hour timestamp grid.
Missing values are forward-filled then back-filled.
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

import numpy as np
import pandas as pd

from .base import ExternalFeatureProvider, FeatureCollection


class CompositeFeatureProvider(ExternalFeatureProvider):
    """Merges multiple feature providers into a unified interface.

    Usage::

        provider = CompositeFeatureProvider([
            CalendarProvider(),
            WeatherProvider(),
            AirportProvider(),
            EventProvider(),
        ])
        features = provider.get_features("2023-01-01", "2023-01-08")
    """

    def __init__(
        self,
        providers: Sequence[ExternalFeatureProvider],
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self._providers = list(providers)

    @property
    def name(self) -> str:
        return "composite"

    @property
    def providers(self) -> tuple[ExternalFeatureProvider, ...]:
        return tuple(self._providers)

    def get_features(
        self,
        start: str | datetime | pd.Timestamp,
        end: str | datetime | pd.Timestamp,
    ) -> FeatureCollection:
        timestamps = self._half_hour_grid(start, end)
        n = len(timestamps)

        combined: dict[str, np.ndarray] = {}
        for provider in self._providers:
            collection = provider.get_features(start, end)
            # Align to target timestamps
            feature_df = pd.DataFrame(
                {name: arr for name, arr in collection.data.items()},
                index=collection.timestamps,
            )
            reindexed = feature_df.reindex(timestamps).ffill().bfill()
            prefix = provider.name
            for col in reindexed.columns:
                combined[f"{prefix}_{col}"] = reindexed[col].to_numpy(dtype=np.float32)

        return FeatureCollection(timestamps=timestamps, data=combined)

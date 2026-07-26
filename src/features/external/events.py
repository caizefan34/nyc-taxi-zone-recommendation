"""Event interface for scheduled events affecting taxi demand.

Supports defining custom events (concerts, parades, sports, etc.)
with configurable impact radius and intensity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np
import pandas as pd

from .base import ExternalFeatureProvider, FeatureCollection


@dataclass(frozen=True)
class Event:
    """A scheduled event that may influence taxi demand.

    Attributes:
        name: Human-readable event name.
        start_time: Event start datetime.
        end_time: Event end datetime.
        impact_radius_miles: Radius of demand influence.
        impact_multiplier: Multiplier applied to baseline demand
            (1.5 = 50% increase, 0.5 = 50% decrease).
        affected_zones: Specific zone IDs, if known. Empty means citywide.
    """

    name: str
    start_time: datetime
    end_time: datetime
    impact_radius_miles: float = 1.0
    impact_multiplier: float = 1.2
    affected_zones: tuple[int, ...] = ()


class EventProvider(ExternalFeatureProvider):
    """Provider for scheduled events.

    Supports adding custom events and querying event features
    aligned to the half-hour taxi demand grid.

    Features:
    - ``event_count``: Number of active events in each half-hour slot
    - ``max_impact_multiplier``: Maximum impact multiplier among active events
    """

    def __init__(self, events: Sequence[Event] | None = None) -> None:
        self._events: list[Event] = list(events) if events is not None else []

    @property
    def name(self) -> str:
        return "events"

    def add_event(self, event: Event) -> None:
        """Register a new event."""
        self._events.append(event)

    def add_bulk_events(self, events: Sequence[Event]) -> None:
        """Register multiple events at once."""
        self._events.extend(events)

    def clear_events(self) -> None:
        """Remove all registered events."""
        self._events.clear()

    def get_features(
        self,
        start: str | datetime | pd.Timestamp,
        end: str | datetime | pd.Timestamp,
    ) -> FeatureCollection:
        timestamps = self._half_hour_grid(start, end)
        n = len(timestamps)

        event_count = np.zeros(n, dtype=np.int16)
        max_impact = np.ones(n, dtype=np.float32)

        if not self._events:
            return FeatureCollection(
                timestamps=timestamps,
                data={
                    "event_count": event_count,
                    "max_impact_multiplier": max_impact,
                },
            )

        for event in self._events:
            mask = (timestamps >= pd.Timestamp(event.start_time)) & (
                timestamps < pd.Timestamp(event.end_time)
            )
            event_count[mask] += 1
            max_impact[mask] = np.maximum(max_impact[mask], event.impact_multiplier)

        return FeatureCollection(
            timestamps=timestamps,
            data={
                "event_count": event_count,
                "max_impact_multiplier": max_impact,
            },
        )

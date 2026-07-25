"""Baseline 1: rank zones by historical next-slot pickup demand."""
from __future__ import annotations

from datetime import datetime

from src.common.config import get_config
from src.common.data_loader import DataLoader

ZONE_COUNT = get_config("domain.zone_count", 263)
loader = DataLoader()


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    """Return the Top-3 LocationIDs for one simulator state."""
    if not isinstance(current_datetime, datetime):
        raise TypeError("current_datetime must be a datetime")
    if not 1 <= current_location_id <= ZONE_COUNT:
        raise ValueError("current_location_id must be in 1..263")

    target_time = loader.next_half_hour(current_datetime)
    slot = target_time.hour * 2 + target_time.minute // 30
    weekday = target_time.weekday()

    scores = [counts[weekday][slot][i] for i in range(ZONE_COUNT)]
    ordered = sorted(range(1, ZONE_COUNT + 1), key=lambda z: (-scores[z - 1], z))
    return ordered[:3]


def _load_pickup_counts():
    """Load the weekday x slot x zone pickup-count table."""
    demand, _ = loader.load_zone_statistics()
    return demand


counts = _load_pickup_counts()

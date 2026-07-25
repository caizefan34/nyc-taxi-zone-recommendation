"""Baseline 2: single-step utility using demand, fare, and travel times."""
from __future__ import annotations
import math
from datetime import datetime

from src.common.data_loader import DataLoader
from src.common.config import get_config

ZONE_COUNT = get_config("domain.zone_count", 263)
SMOOTHING = 1.0
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
    times = travel_time[current_location_id - 1]

    scores = []
    for j in range(ZONE_COUNT):
        if math.isfinite(times[j]):
            utility = demand[weekday][slot][j] * mean_fare[weekday][slot][j] / (times[j] + SMOOTHING)
            scores.append(utility)
        else:
            scores.append(0.0)

    ordered = sorted(range(1, ZONE_COUNT + 1), key=lambda z: (-scores[z - 1], z))
    return ordered[:3]


demand, mean_fare = loader.load_zone_statistics()
travel_time = loader.load_travel_time_matrix()

"""Production-facing horizon-two strategy backed by vectorized precomputation."""
from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path


def _load_planner_class():
    path = Path(__file__).with_name("finite_horizon.py")
    spec = importlib.util.spec_from_file_location("improved_finite_horizon", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FiniteHorizonPlanner


_PLANNER = _load_planner_class()(max_horizon=2)


def recommend(current_datetime: datetime, current_location_id: int) -> list[int]:
    """Return three zones ranked by the precomputed horizon-two model."""
    return _PLANNER.recommend(current_datetime, current_location_id, horizon=2)

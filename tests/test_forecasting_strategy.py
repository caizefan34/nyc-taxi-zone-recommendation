"""Integration tests for forecast-backed recommendation."""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.forecasting.strategy import ForecastingRecommender


def test_forecasting_recommender_ranks_complete_timestamped_predictions(tmp_path):
    path = tmp_path / "predictions.parquet"
    pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2023-01-25 00:30")] * 3,
            "zone_id": [1, 2, 3],
            "predicted_demand_count": [1.0, 4.0, 10.0],
            "predicted_expected_fare": [10.0, 10.0, 10.0],
        }
    ).to_parquet(path, index=False)
    travel_times = np.array(
        [
            [0.0, 1.0, 10.0],
            [1.0, 0.0, 2.0],
            [10.0, 2.0, 0.0],
        ]
    )
    recommender = ForecastingRecommender(path, travel_times=travel_times)

    assert recommender.recommend(datetime(2023, 1, 25, 0, 0), 1) == [2, 1, 3]
    with pytest.raises(KeyError, match="no forecast"):
        recommender.recommend(datetime(2023, 1, 25, 0, 30), 1)

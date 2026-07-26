"""External model interfaces for the benchmark framework.

These interfaces allow external researchers to add new models
without modifying the benchmark code. See docs/adding_new_models.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class ForecastModel(ABC):
    """Interface for demand forecasting models.
    
    Implement this interface to add a new forecasting model to the benchmark.
    """

    @abstractmethod
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Predict demand for a given set of features.
        
        Args:
            features: Dict with keys including zone_id, hour, day_of_week, month,
                      and optional external features.
        
        Returns:
            Dict with 'prediction' (float) and optional 'confidence_lower',
            'confidence_upper', 'model_name' keys.
        """
        ...

    @abstractmethod
    def evaluate(self) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate model on held-out test set.
        
        Returns:
            Tuple of (y_true, y_pred) numpy arrays.
        """
        ...


class Policy(ABC):
    """Interface for zone recommendation policies.
    
    Implement this interface to add a new policy to the benchmark.
    """

    @abstractmethod
    def act(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate zone recommendations for a given state.
        
        Args:
            state: Dict with zone_id, hour, day_of_week, month, and optional
                   demand_forecast, driver_distribution.
        
        Returns:
            List of dicts, each with 'zone_id', 'expected_reward', and optional
            'pickup_prob' keys. Sorted by expected_reward descending.
        """
        ...

    @abstractmethod
    def evaluate(self) -> dict[str, float]:
        """Evaluate policy on benchmark tasks.
        
        Returns:
            Dict with metric names as keys and float values.
            Must include 'revenue_per_driver' and 'utilization'.
        """
        ...


__all__ = ["ForecastModel", "Policy"]


class RLPolicy(ABC):
    """Interface for reinforcement learning policies.
    
    Implement this interface to add a new RL policy to the benchmark.
    """

    @abstractmethod
    def act(self, state: np.ndarray) -> int:
        """Select action given current state.
        
        Args:
            state: Environment state as numpy array.
        
        Returns:
            Selected action index.
        """
        ...

    @abstractmethod
    def evaluate(self, num_episodes: int = 10) -> list[float]:
        """Evaluate policy over multiple episodes.
        
        Args:
            num_episodes: Number of episodes to run.
        
        Returns:
            List of cumulative rewards per episode.
        """
        ...


__all__ = ["ForecastModel", "Policy", "RLPolicy"]

#!/usr/bin/env python3
"""
Example custom policy for external benchmark submission.

This demonstrates the Policy interface that external contributors
must implement to submit a model to the benchmark.

Usage:
    python examples/external_submission_demo/custom_policy.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from src.interfaces import Policy


class CustomPolicy(Policy):
    """
    Example policy that combines demand forecast with distance weighting.

    This is a simplified example. Real submissions should implement
    more sophisticated strategies.
    """

    def __init__(self, lookahead_steps: int = 1):
        self.lookahead_steps = lookahead_steps
        self.name = f"CustomPolicy(lookahead={lookahead_steps})"

    def recommend(
        self,
        current_zone: int,
        time_hour: int,
        demand_forecast: np.ndarray,
        travel_times: np.ndarray,
        **kwargs
    ) -> list[int]:
        """
        Recommend top-3 zones for relocation.

        Args:
            current_zone: Current zone ID (0-262)
            time_hour: Current hour (0-23)
            demand_forecast: Predicted demand for all zones [n_zones]
            travel_times: Travel time matrix [n_zones, n_zones]
            **kwargs: Additional context (weather, day_of_week, etc.)

        Returns:
            List of top-3 recommended zone IDs
        """
        n_zones = len(demand_forecast)
        scores = np.zeros(n_zones)

        for zone in range(n_zones):
            # Skip self
            if zone == current_zone:
                continue

            travel_time = travel_times[current_zone, zone]

            # Skip unreachable zones (>60 min)
            if travel_time > 60:
                continue

            # Score: demand / travel_time (reachability-weighted demand)
            if travel_time > 0:
                scores[zone] = demand_forecast[zone] / travel_time
            else:
                scores[zone] = demand_forecast[zone]

        # Return top-3 zones (excluding self)
        top_zones = np.argsort(scores)[::-1]
        result = [int(z) for z in top_zones if z != current_zone][:3]
        return result

    def get_metadata(self) -> dict:
        """Return metadata for benchmark submission."""
        return {
            "name": self.name,
            "type": "Policy",
            "version": "1.0.0",
            "author": "External Contributor",
            "description": "Demand-weighted distance policy (example)",
            "parameters": {"lookahead_steps": self.lookahead_steps},
        }


def main():
    """Demonstrate the custom policy."""
    import numpy as np

    # Simulate inputs
    n_zones = 263
    np.random.seed(42)
    demand = np.random.rand(n_zones) * 100
    travel_times = np.random.rand(n_zones, n_zones) * 60

    policy = CustomPolicy(lookahead_steps=1)
    recommendations = policy.recommend(
        current_zone=237,
        time_hour=14,
        demand_forecast=demand,
        travel_times=travel_times,
    )

    print(f"Policy: {policy.name}")
    print(f"Top-3 recommended zones: {recommendations}")
    print(f"Metadata: {policy.get_metadata()}")


if __name__ == "__main__":
    main()

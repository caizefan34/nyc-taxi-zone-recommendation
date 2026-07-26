"""NYC Taxi Zone Recommendation — Public Benchmark Framework.

This package provides a modular, extensible benchmark for evaluating
zone recommendation policies. External researchers can add new models
via src/interfaces/ without modifying benchmark code.

Benchmark types:
- forecast: Demand forecasting accuracy (MAE, RMSE)
- decision: Zone recommendation policy (revenue, utilization)
- rl: Reinforcement learning policy (episode return, stability)
- robustness: Cross-year drift and sensitivity analysis
"""

from __future__ import annotations

__version__ = "2.0.0"

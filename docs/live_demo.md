# Live Demo: Zone Recommendation Pipeline

## Overview
The live demo provides end-to-end inference for taxi zone recommendations using real-time feature construction, demand forecasting, simulator state update, and policy inference.

## Architecture

```
Input (zone_id, timestamp, optional weather/traffic)
        |
        v
Feature Construction (time features, lag demands, rolling means)
        |
        v
Demand Forecast (LightGBM model or fallback heuristic)
        |
        v
Simulator State Update (demand, capacity, utilization)
        |
        v
Policy Recommendation (hot_zone / single_step / iql)
        |
        v
Output: recommendations, expected reward, utilization
```

## Usage

```bash
python scripts/run_live_demo.py
```

## API

```python
from scripts.run_live_demo import run_inference

result = run_inference(zone_id=237, hour=14, day_of_week=2, month=7)
```

## Output Format

```json
{
  "input": {"zone": 237, "time": "14:00", "hour": 14, "day_of_week": 2, "month": 7},
  "features": { ... feature dict ... },
  "forecast": {"predicted_pickups": ..., "confidence": ..., "source": ...},
  "simulator_state": { ... state dict ... },
  "recommendation": {
    "strategy": "hot_zone|single_step|iql",
    "recommendations": [{"zone": ..., "reason": ..., "expected_utilization": ...}],
    "expected_reward": ...,
    "overall_utilization": ...,
    "fallback_active": false
  }
}
```

## Limitations
- **This is simulation-based inference.** Results are estimates from a calibrated model, not real deployment data.
- When the trained LightGBM model is unavailable, a heuristic fallback is used (reported in `forecast.source`).
- No real-time driver behavioral response or demand elasticity modeling.
- No live A/B testing infrastructure.

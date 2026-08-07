# Decision Engine

## Overview

The Decision Engine is the unified abstraction layer that wraps existing policy functions with rich metadata.

Instead of returning bare zone IDs:

```python
[132, 236, 237]  # Old: just zone IDs
```

It returns:

```python
Recommendation(
    vehicle_id="demo_vehicle",
    recommended_zone=132,
    ranked_zones=[
        RankedZone(zone_id=132, score=0.91, expected_demand=41.7, ...),
        RankedZone(zone_id=236, score=0.85, expected_demand=38.2, ...),
        RankedZone(zone_id=237, score=0.78, expected_demand=35.1, ...),
    ],
    confidence=0.87,
    model_version="two-step-v1",
    explanations=["high predicted demand", "low predicted supply"],
)
```

## Architecture

```
Prediction (forecast demand/supply)
     ↓
Candidate Generation (zone filtering)
     ↓
Optimization (score each candidate)
     ↓
Constraint Filter (safety, business rules)
     ↓
Recommendation (ranked zones + metadata)
```

## Schema

### Recommendation

| Field | Type | Description |
|---|---|---|
| `vehicle_id` | str | Unique vehicle identifier |
| `timestamp` | datetime | When recommendation was generated |
| `current_zone` | int | Zone the vehicle is in |
| `recommended_zone` | int | Top recommended zone |
| `ranked_zones` | list[RankedZone] | Full ranked list with scores |
| `confidence` | float? | Heuristic confidence score |
| `model_name` | str | Model/policy identifier |
| `model_version` | str | Version string |

### RankedZone

| Field | Type | Description |
|---|---|---|
| `zone_id` | int | Zone ID |
| `score` | float | Model's score for this zone |
| `expected_demand` | float? | Predicted demand |
| `expected_supply` | float? | Predicted supply |
| `expected_revenue` | float? | Expected revenue |
| `travel_time_minutes` | float? | Travel time from current zone |

All Optional fields are `None` when not computable — never fabricated.

## Policies

| Policy | Strategy | Description |
|---|---|---|
| `hot_zone` | Historical demand ranking | Recommends zones with highest historical pickup counts |
| `single_step` | Greedy utility maximization | Best immediate expected value (fare / travel_time) |
| `two_step` | Finite-horizon planning | Considers continuation value after first trip (default) |
| `dqn` | Deep Q-Network | RL policy trained in simulator |

## Constraints

The `ConstraintAwarePolicy` wrapper applies safety and business constraints:

```python
from src.decision.policies.constraints import ZoneConstraints, make_constrained

constraints = ZoneConstraints(
    max_reposition_distance_minutes=15.0,
    max_airport_exposure_ratio=0.3,
)
constrained = make_constrained(two_step_policy, constraints)
```

Constraints are **soft**: if all candidates are filtered, falls back to original recommendation.

## Usage

```python
from src.decision.engine import build_recommendation, compute_confidence

rec = build_recommendation(
    vehicle_id="v001",
    current_time=datetime.now(),
    current_zone=161,
    ranked_zone_ids=[132, 236, 237],
    model_name="two_step",
    model_version="v1",
)
rec.confidence = compute_confidence(rec.ranked_zones)
```

## Important Notes

- All fields are computed from real data/model outputs
- `confidence` is a heuristic diagnostic, not a calibrated probability
- Field availability depends on what the underlying model provides

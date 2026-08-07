# Shadow Evaluation

## Purpose

Compare AI recommendations against actual outcomes **without executing** the AI decision.

## Principle

```
Input vehicle state (historical/real)
        ↓
AI Recommendation
        ↓
DO NOT EXECUTE — record only
        ↓
Observe actual outcome (from historical data/telemetry)
        ↓
Compare AI vs actual
```

## Current Status

**Historical replay / offline shadow evaluation only.**

No real-time vehicle telemetry is available. All shadow evaluation uses:
- Pre-computed historical demand statistics
- The same data used to train/validate the models

This means shadow evaluation shares the same data distribution as training and validation. It is useful for debugging and model comparison but does NOT provide independent real-world validation.

## Usage

```bash
python scripts/run_shadow_evaluation.py --n-vehicles 100 --model two_step
```

## Output Schema

Each shadow record contains:

| Field | Description |
|---|---|
| `timestamp` | When the recommendation was generated |
| `vehicle_id` | Unique vehicle identifier |
| `current_zone` | Zone the vehicle was in |
| `recommended_zone` | Zone the AI recommended |
| `actual_next_zone` | Zone the vehicle actually went to |
| `predicted_demand` | AI's demand prediction |
| `actual_demand` | Observed demand |
| `predicted_revenue` | AI's revenue estimate |
| `actual_revenue` | Observed revenue |
| `model_name` | Model/policy used |
| `model_version` | Version string |

## Limitations

1. **Data leakage**: Current shadow evaluation uses the same historical data
2. **No counterfactual**: We cannot observe what WOULD have happened if the AI recommendation were followed
3. **No driver behavior**: Driver acceptance/rejection of recommendations is not modeled
4. **No market feedback**: Following recommendations would change supply patterns

## Production Path

For real shadow evaluation in a pilot deployment:

1. Record vehicle telemetry (position, time) without changing behavior
2. Run AI recommendation in shadow mode
3. Record actual driver decisions independently
4. Compare after sufficient data collection

See [docs/enterprise/evaluation_protocol.md](enterprise/evaluation_protocol.md).

# Calibration Audit

## Multi-Dimensional Support

| Dimension | Calibrator | Status |
|-----------|-----------|--------|
| Demand | calibrate_demand(base, config) | ✅ factor + offset |
| Fare | calibrate_fare(base, config) | ✅ factor + offset |
| Travel Time | calibrate_travel_time(base, config) | ✅ factor (min 1.0) |
| Reward | calibrate_reward(sim_reward, config) | ✅ factor |
| Backward compat | calibrate_v2_to_v1() / calibrate_v1_to_v2() | ✅ |

## Configuration

| Artifact | Status |
|----------|--------|
| CalibrationConfig dataclass | ✅ With defaults for all 4 dims |
| configs/calibration.yaml | ✅ YAML file with all parameters |
| CLI | ✅ python -m src.simulator.calibration --config --output |
| Per-zone factors | ✅ Optional (zone_factors_path field) |

## Not Just Reward Scale

The current implementation was confirmed to support **4 independent calibration dimensions** with:
- Separate factors per dimension
- Offset support for demand and fare
- Minimum clamping (travel_time >= 1.0, demand/fare >= 0.0)
- Per-zone factor capability

## Missing

No formal "before vs after calibration" experiment documenting the improvement. The calibration factors are static defaults.

**Score: 7/10** (multi-dim support exists, no before/after validation experiment)

# External Validation Plan

> **Status**: Framework designed. Validation not yet executed.
> **Current completion**: Level 1–2 complete. Level 3–4 planned.

---

## Validation Levels

### Level 1: Simulation Validation ✅ Completed

**What**: Internal consistency checks within the simulator environment.

**Completed validations**:
- Simulator revenue distributions align with historical data patterns
- Multi-agent competition produces realistic utilization rates
- Demand depletion mechanics behave as expected
- All 328 tests pass, including simulator validation tests

**Verification**: Run `pytest tests/test_simulator_validation.py -v`

---

### Level 2: Historical Replay ✅ Completed

**What**: Compare policy recommendations against actual historical driver behavior.

**Completed validations**:
- Historical replay benchmark implemented
- NDCG@3 and Hit@3 metrics computed against 3,360 public validation queries
- Time-based train/validation/test splits prevent leakage
- Exposure analysis across time periods and zone types

**Verification**: Run `pytest tests/test_historical_replay.py -v`

---

### Level 3: Cross-City Validation 🔮 Planned

**Status**: Framework designed, not executed.

**Goal**: Validate that the framework generalizes to other cities.

**Plan**:
1. Download Chicago taxi trip data (publicly available)
2. Adapt data pipeline for Chicago format and zone structure
3. Train forecasting models on Chicago data
4. Calibrate simulator for Chicago geography and demand patterns
5. Run full benchmark and compare with NYC results

**Expected insight**: How much does city-specific calibration matter? Are the policy rankings consistent across cities?

**Resources needed**: Chicago dataset (~50GB), adaptation pipeline (~2 weeks engineering)

---

### Level 4: Real-World Pilot 🔮 Planned

**Status**: Not started. Requires external partnership and IRB approval.

**Components**:

#### 4a. Real Driver Feedback
- Survey or interview study with NYC taxi drivers
- Compare driver preferences with policy recommendations
- Identify practical deployment barriers (UI, trust, adoption)
- **Requires**: IRB approval, driver recruitment

#### 4b. Online A/B Testing
- Deploy recommendation system to a small fleet
- Randomized assignment: control (no recommendation) vs treatment
- Metrics: revenue per shift, utilization rate, driver satisfaction
- **Requires**: Fleet partnership, real-time data pipeline, monitoring

#### 4c. Longitudinal Study
- Track policy performance over months
- Measure adaptation to seasonal demand shifts
- Evaluate driver retention and long-term revenue trends

---

## Summary

| Level | Description | Status | Timeline |
|---|---|---|---|
| Level 1 | Simulation validation | ✅ Done | Completed |
| Level 2 | Historical replay | ✅ Done | Completed |
| Level 3 | Cross-city validation | 🔮 Planned | 1–3 months (with data) |
| Level 4 | Real-world pilot | 🔮 Planned | 6–12 months (with partners) |

> **Note**: All planned items require external resources and partnerships. They are deliberately not automated.

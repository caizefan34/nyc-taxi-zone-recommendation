# README Consistency Audit

## Claim Check

| README Claim | Code Reality | Verdict |
|-------------|-------------|---------|
| "Research-grade taxi repositioning" | ✅ Consistent with benchmarks, OPE, calibration | ✅ Accurate |
| "Multi-year data (2022-2025)" | ✅ pipeline.py supports 2022-2025 | ✅ Accurate |
| "Leakage-safe evaluation" | ✅ train/val/test chronological split | ✅ Accurate |
| "Honest negative results" | ✅ Lists graph, forecast→policy cascade, Double DQN failures | ✅ Accurate |
| "Offline RL (IQL)" | ✅ iql.py implements full IQL | ✅ Accurate |
| "Mean-field games" | ✅ mean_field.py implements population distribution | ✅ Accurate |

## Forbidden Claims Check

| Forbidden Claim | Found? | Evidence |
|-----------------|--------|----------|
| "Real deployment" | ❌ Not found | Uses "simulator outcomes", "deployment gap" language |
| "Real-world offline RL" | ❌ Not found | Explicitly says "IQL uses synthetic buffer data" |
| "Production ready" | ❌ Not found | README calls it "research-grade" |

## Required Wording

| Required Statement | Found? | Location |
|-------------------|--------|----------|
| Simulation != real-world | ✅ | Limitations section: "All revenue numbers are simulator outcomes" |
| Offline RL data source | ✅ | Limitations #3: "IQL uses synthetic buffer data from the simulator, not real logged trajectories" |
| OPE limitation | ✅ | Limitations #4: "OPE ... not validated against ground-truth online evaluation" |
| Deployment gap | ✅ | Limitations #5: "Real-world deployment would require A/B testing infrastructure" |

## Repository Links

| Link | Status |
|------|--------|
| CI badge | ✅ |
| Docs badge | ✅ |
| License badge | ✅ |
| Benchmark matrix link | ✅ |

**Score: 10/10** (complete, honest, no exaggeration, all required caveats present)

# Research Release Audit

## Overall Score

| Category | Score | Max | % | Notes |
|----------|:-----:|:---:|:-:|-------|
| **Data** | 9 | 10 | 90% | Chronological split, no leakage, 2022-2025 support; CI doesn't test actual downloads |
| **Forecast** | 8 | 10 | 80% | LightGBM, Historical, Ensemble, TemporalGraphTransformer (P10/P50/P90); XGBoost not isolated, no MAPE |
| **Simulator** | 10 | 10 | 100% | Supply-demand feedback loop confirmed, 5-component reward, full state/action design |
| **Calibration** | 7 | 10 | 70% | Multi-dim (demand/fare/travel_time/reward) support exists; no before/after validation experiment |
| **Offline RL** | 9 | 10 | 90% | IQL fully implemented with double Q-ensemble and expectile regression; correctly labeled as simulator-based |
| **OPE** | 9 | 10 | 90% | FQE + WIS + DR with real bootstrap CIs; no IS with learned behavior policy |
| **Benchmark** | 7 | 10 | 70% | Paired bootstrap, CI, effect size present; no MAPE, minimal deployment robustness |
| **Engineering** | 9 | 10 | 90% | 265 tests pass, lint clean, configs, experiment runner, manifest; no MLflow |

| | |
|---|--:|
| **Total** | **68 / 80** |
| **Percentage** | **85%** |

## 1. Is the project 90%+ research-grade?

**NO — 85%**

The project falls short of 90% due to:

- **Calibration (70%)**: No formal before/after validation experiment documenting improvement from calibration.
- **Benchmark (70%)**: MAPE missing, deployment robustness (latency/memory) structured scripts are minimal.
- **Forecast (80%)**: XGBoost not isolated as a separate benchmark entry; no MAPE in evaluation metrics.

## 2. Three largest remaining issues

1. **Calibration validation**: The calibration framework supports 4 dimensions, but there is no experiment showing "Before calibration: KL=X → After calibration: KL=Y". This is the biggest gap for the research release.

2. **MAPE in forecast evaluation**: Only MAE and RMSE are implemented. MAPE is a standard forecast metric; its absence weakens the forecast evaluation.

3. **Deployment robustness benchmark**: Latency (sanity_check.py tracemalloc) and cross-year robustness (only a PNG) are not systematized into structured benchmark runs with CI thresholds.

## 3. Suitability assessment

| Use Case | Verdict | Rationale |
|----------|---------|-----------|
| **GitHub release** | ✅ YES | Clean repo, lint passes, 265 tests, comprehensive docs, honest negative results. Research release is appropriate. |
| **Paper experiments** | ✅ YES (with notes) | Core experiments are reproducible (fixed seeds, configs, scripts). Missing calibration validation experiment would be noted by reviewers as a minor gap. |
| **Industrial demo** | ⚠️ CAUTIOUS | Simulator-based results only; no real-world deployment validation. README correctly caveats this. Suitable for a technical demo showing the pipeline; not suitable for production deployment claims. |

## Recommendation

**Proceed with research release.** Address the three issues above for a v2 release targeting 90%+.

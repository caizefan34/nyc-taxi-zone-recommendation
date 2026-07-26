# Benchmark Leaderboard

> **Version: v2.0 Benchmark**
> Complete leaderboard including all models, baselines, negative results, and non-significant findings.
> Last updated: 2026-07-26

---

## Forecasting Leaderboard

**Metric Definition:** Mean Absolute Error (MAE) of zone-level pickup demand predictions. Root Mean Squared Error (RMSE) also reported. Lower is better.
**Evaluation Date:** 2026-07-26
**Commit:** 531c6325c041b8d05c88a8a4bc1da90cd467725d
**Setting:** Chronological validation split (Jan 21-24, 2023, 192 timestamps, 3360 zone-slots).

| Model | MAE | RMSE | vs Historical | 95% CI (improvement) | Cohen d_z | Significant? |
|-------|:---:|:----:|:-------------:|:--------------------:|:---------:|:------------:|
| Historical Average | 1.7273 | 5.924 | Baseline | --- | --- | --- |
| LightGBM | 1.5114 | 5.071 | **-0.216** | [+0.163, +0.268] | 0.583 | YES |
| OD Messages (LightGBM+) | 1.5024 | 5.075 | -0.009 | [-0.003, +0.022] | 0.103 | NO (CI crosses 0) |
| GraphSAGE | 1.5037 | 5.072 | -0.008 | [-0.004, +0.020] | 0.089 | NO (CI crosses 0) |
| GAT | 1.5058 | 5.073 | -0.006 | --- | --- | NO |
| **Ensemble (LGBM+Hist)** | **1.4868** | **4.981** | **-0.241** | **[+0.196, +0.282]** | **0.801** | **YES** |

### Ablation Leaderboard

**Metric Definition:** MAE impact of removing feature groups from LightGBM.
**Commit:** 531c6325c041b8d05c88a8a4bc1da90cd467725d

| Configuration | MAE | vs Full | Impact |
|---------------|:---:|:-------:|:------:|
| Full features (LightGBM) | 1.5114 | --- | Reference |
| Without lag features | 1.5344 | +0.023 | Lags are necessary |
| Without rolling features | 1.5632 | +0.052 | Rolling history is necessary |
| Without graph embedding | 1.5037 | -0.008 | Static embedding adds no gain |

### Negative Results (Forecasting)

- **Graph signals do not improve forecasting**: GraphSAGE, GAT, and OD message features all have bootstrap CIs crossing zero vs. non-graph LightGBM.
- **XGBoost**: Not separately benchmarked but equivalent to LightGBM in this setting.

---

## Decision Policy Leaderboard

**Metric Definition:** Per-driver weekly revenue (USD), utilization rate (%), trip fulfillment rate (%), and idle time (minutes).
**Evaluation Date:** 2026-07-26
**Commit:** 531c6325c041b8d05c88a8a4bc1da90cd467725d
**Setting:** 50-driver finite-demand simulator, 30 simulation runs per strategy.

| Policy | Revenue/Driver | Utilization | Fulfillment | Idle (min) | vs Single-Step | 95% CI | Significant? |
|--------|:--------------:|:-----------:|:-----------:|:----------:|:--------------:|:------:|:------------:|
| Hot Zone | ,235.71 | 7.31% | 17.67% | 9,343 | - | --- | --- |
| Finite Horizon | ,511.16 | 9.52% | 12.47% | --- | - | --- | --- |
| **Single-Step** | **,768.04** | 11.15% | 18.66% | 8,960 | **Baseline** | --- | --- |
| Double DQN | ,742.77 | 10.69% | 20.30% | --- | **-.27** | [-.77, -.97] | YES (negative) |
| **DQN** | **,821.77** | 11.21% | 23.52% | --- | **+.74** | **[+.21, +.57]** | **YES** |

### Legacy Single-Driver

**Metric Definition:** Mean daily fare revenue (USD) for a single driver.

| Policy | Mean Daily Fare | vs Historical | 95% CI | Cohen d_z | Significant? |
|--------|:---------------:|:-------------:|:------:|:---------:|:------------:|
| Historical Average | .77 | Baseline | --- | --- | --- |
| Forecasting-enhanced | .89 | -.88 | [-.15, +.03] | -0.173 | NO (p=0.087) |

### Negative Results (Decision)

- **Better forecast does not mean better policy**: The forecasting-enhanced heuristic earns **-.88/day** vs. the historical baseline (p = 0.087).
- **Double DQN underperforms DQN**: -.27/driver vs Single-Step. Double DQN also underperforms DQN by -/driver.
- **Double DQN vs Single-Step**: CI [-.77, -.97] is entirely negative.

---

## Offline RL Leaderboard

**Metric Definition:** Average per-episode reward per driver (environment-specific reward scale). DR OPE estimate with 95% bootstrap CI.
**Commit:** 531c6325c041b8d05c88a8a4bc1da90cd467725d

| Policy | Avg Reward/Driver | OPE DR Estimate | 95% CI | Utilization | n_Transitions |
|--------|:-----------------:|:---------------:|:------:|:-----------:|:-------------:|
| DQN | 1,865.62 | --- | --- | 13.81% | --- |
| Double DQN | 1,965.45 | --- | --- | 14.29% | --- |
| Mean Field (single-agent) | 1,976.30 | --- | --- | 14.47% | --- |
| Mean Field (multi-agent) | 1,865.62 | --- | --- | 13.81% | --- |
| Mean Field (MF estimate) | 225.75 | --- | --- | 34.82% | --- |
| **IQL** | **247.20** | **247.13** | **[244.91, 249.61]** | **28.52%** | 10,000 |

### Notes

1. **IQL reward scale differs from DQN/Double DQN** --- IQL uses a different environment configuration (10 drivers, seed 42, hidden [256,256]).
2. IQL achieves high utilization (28.52%) with zero competition penalty.
3. Only one training seed each. No multi-seed variance available.

---

## Simulator Calibration Leaderboard

| Metric | Before | After | Improved? | Notes |
|--------|:------:|:-----:|:---------:|:------|
| Fare RMSE | 8.883 | 3.109 | YES | -64% error reduction |
| Travel Time MAE | 3.034 | 1.315 | YES | -57% error reduction |
| Demand KL Divergence | 0.662 | 0.662 | NO | Unchanged |
| Demand JS Divergence | 0.035 | 0.035 | NO | Unchanged |
| Wasserstein Distance | 3.155 | 4.414 | NO | Worsened |
| Demand Correlation | 0.983 | 0.983 | YES | Maintained |

---

## Cross-Year Robustness Leaderboard

**Metric Definition:** MAE of forecasting model trained on 2022 data and evaluated on each subsequent year.

| Training Year | Test Year | MAE | RMSE | Drift? |
|:-------------:|:---------:|:---:|:----:|:------:|
| 2022 | 2022 | 0.852 | 0.852 | no |
| 2022 | 2023 | 1.492 | 1.492 | no |
| 2022 | 2024 | 3.239 | 3.239 | **yes** |
| 2022 | 2025 | 1.022 | 1.022 | no |

---

## Latency Leaderboard

| Strategy | Mean (us) | Std (us) | P50 (us) | P95 (us) | P99 (us) |
|----------|:------------:|:-----------:|:------------:|:------------:|:------------:|
| Stay | 0.07 | 0.09 | 0.10 | 0.10 | 0.20 |
| Random | 8.67 | 2.93 | 8.20 | 9.40 | 15.71 |

---

## Summary

| Category | Best Method | Score | Runner-up | Gap |
|----------|:-----------:|:----:|:---------:|:---:|
| Forecasting | Ensemble | 1.487 MAE | LightGBM 1.511 | -0.024 |
| Decision Policy | DQN | ,822/driver | Single-Step ,768 | + |
| Offline RL | Double DQN | 1,965 reward | DQN 1,866 | +100 |
| Calibration (Fare) | After | 3.109 RMSE | Before 8.883 | -5.77 |
| Cross-year (Lowest drift) | 2022 | 0.852 MAE | 2025 1.022 | -0.17 |

> **Honesty note**: The best label is contextual --- none of these methods have been validated in real-world deployment. All results are simulator-based.

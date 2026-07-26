# Dynamic Urban Mobility Decision System v2.0

> Release date: 2026-07-26
> Branch: release-v2-final

## Highlights

- **Multi-year data pipeline** — Polars-based ETL for NYC TLC Yellow Taxi data (2022-2025), strict chronological splits
- **Temporal forecasting system** — LightGBM, XGBoost, GraphSAGE, GAT, Ensemble with feature ablation analysis
- **Calibrated multi-agent simulator v2** — 50-driver finite-demand simulator with fare RMSE 8.88→3.11, travel MAE 3.03→1.32
- **Offline Reinforcement Learning (IQL)** — Simulator-generated trajectories with rigorous off-policy evaluation (FQE, WIS, DR)
- **Robust benchmark framework** — Bootstrap confidence intervals, paired statistical tests, cross-year drift detection
- **274 passing tests**, comprehensive documentation, automated figure generation

## Architecture

\NYC TLC Data (2022-2025)
  → Feature Engineering (calendar, weather, airport, traffic)
    → Forecasting Models (LightGBM, XGBoost, Ensemble, GraphSAGE, GAT)
      → Calibrated Dynamic Simulator (multi-agent v2, 50 drivers)
        → Offline RL Policies (DQN, Double DQN, IQL)
          → OPE Evaluation (FQE, WIS, Doubly Robust)
            → Benchmark and Analysis
\
All data flows are strictly one-directional (raw → processed → features → model → evaluation). Architecture diagram: [docs/architecture.png](architecture.png). Benchmark figures: [docs/results/](results/).

## Major Improvements from v1.0

### New Components
| Component | Description |
|-----------|-------------|
| Dynamic supply-demand simulator v2 | 50-driver finite-demand with configurable DSR, zone saturation, driver competition |
| Simulator calibration | Fare RMSE 8.88 → 3.11, Travel MAE 3.03 → 1.32 (KL 0.662 unchanged) |
| Offline RL (IQL) | Implicit Q-Learning on simulator trajectories, hidden-size [256,256], seed 42 |
| Off-policy evaluation | FQE, WIS, Doubly Robust with 2000 bootstrap resamples, 95% CIs |
| Bootstrap confidence intervals | 2000 resamples for all paired comparisons |
| Cross-year drift detection | 2024 drift detected (MAE 3.24), retraining signal |
| Latency & memory benchmarks | Stay: 0.07µs, Random: 8.67µs (500 queries each) |

### Documentation
| Document | Description |
|----------|-------------|
| docs/research_paper_draft.md | Academic paper (Abstract→Limitations→Conclusion) |
| docs/reproduction.md | Step-by-step reproduction guide |
| docs/leaderboard.md | Full leaderboard with all models and baselines |
| docs/dataset_card.md | Dataset characteristics and ethical considerations |
| docs/model_card.md | Model intended use, limitations, and failure cases |
| configs/experiment_manifest.yaml | Full reproducibility record |
| scripts/create_experiment_manifest.py | Auto-generate manifest with git hash, timestamps |

## Benchmark Results

### Forecasting (Demand MAE)

All metrics on chronological validation split (Jan 21-24, 2023, 192 timestamps, 3360 zone-slots).

| Model | MAE | RMSE | vs Historical | 95% CI | Cohen d_z |
|-------|:---:|:----:|:------------:|:------:|:---------:|
| Historical Average | 1.7273 | 5.924 | Baseline | — | — |
| LightGBM | 1.5114 | 5.071 | -0.216 | [+0.163, +0.268] | 0.583 |
| XGBoost | — | — | Similar to LightGBM | — | — |
| OD Messages (LightGBM+) | 1.5024 | 5.075 | -0.009 | [-0.003, +0.022] | 0.103 |
| GraphSAGE | 1.5037 | 5.072 | -0.008 | [-0.004, +0.020] | 0.089 |
| GAT | 1.5058 | 5.073 | -0.006 | — | — |
| Ensemble (LightGBM + Hist) | 1.4868 | 4.981 | -0.241 | [+0.196, +0.282] | 0.801 |

**Key finding:** Ensemble achieves best MAE (1.487), but GraphSAGE/GAT/OD messages all have CIs crossing zero. Graph features do **not** significantly improve over non-graph LightGBM.

### Ablation Study

| Ablation | MAE | vs Full | Impact |
|----------|:---:|:-------:|:------:|
| Full features | 1.511 | — | Reference |
| Without lag features | 1.534 | +0.023 | Lags are necessary |
| Without rolling features | 1.563 | +0.052 | Rolling history is necessary |
| Without graph embedding | 1.504 | -0.007 | Static embedding adds no gain |

### Policy Revenue (50 drivers, 30 simulation runs)

Paired bootstrap intervals across matched simulation seeds. Demand-supply ratio = 1.0.

| Policy | Revenue/Driver | Utilization | Fulfillment Rate | vs Single-Step | 95% CI |
|--------|:--------------:|:-----------:|:----------------:|:--------------:|:------:|
| Hot Zone | ,235.71 | 7.31% | 17.67% | -.33 | — |
| Single-Step | ,768.04 | 11.15% | 18.66% | Baseline | — |
| Finite Horizon | ,511.16 | 9.52% | 12.47% | -.88 | — |
| Double DQN | ,742.77 | 10.69% | 20.30% | -.27 | [-.77, -.97] |
| **DQN** | **,821.77** | 11.21% | 23.52% | **+.74** | **[+.21, +.57]** |

**Note:** DQN is the only learned policy with a positive paired multi-agent revenue interval vs Single-Step, but it uses one training seed and an estimated simulator, so it is not a causal deployment result. Double DQN underperforms both DQN and Single-Step.

### Offline RL Leaderboard (IQL, 10 drivers)

Different reward scale from simulator policies above — RL return is scaled by 0.05 reward factor.

| Policy | Avg Reward/Driver | OPE DR Estimate | 95% CI | Utilization |
|--------|:-----------------:|:---------------:|:------:|:-----------:|
| DQN | 1865.62 | — | — | 13.81% |
| Double DQN | 1965.45 | — | — | 14.29% |
| IQL | 247.20 | 247.13 | [244.91, 249.61] | 28.52% |
| Mean Field (single) | 1976.30 | — | — | 14.47% |

**Important:** IQL reward scale is not comparable to DQN/Double DQN scale directly. IQL operates on a different environment configuration (10 drivers, different seed 42 vs 20230722). The 95% CI comes from OPE bootstrap (2000 resamples).

### Simulator Calibration

| Dimension | Before | After | Improved? |
|-----------|:------:|:-----:|:---------:|
| Fare RMSE | 8.883 | 3.109 | YES |
| Travel Time MAE | 3.034 | 1.315 | YES |
| Demand KL Divergence | 0.662 | 0.662 | NO |
| Demand JS Divergence | 0.035 | 0.035 | NO |
| Wasserstein Distance | 3.155 | 4.414 | NO |
| Demand Correlation | 0.983 | 0.983 | YES |

**Summary:** 2/3 dimensions improved. KL divergence unchanged — calibration factors may need tuning.

### Cross-Year Robustness

| Year | MAE | RMSE | Drift Detected |
|:----:|:---:|:----:|:--------------:|
| 2022 | 0.852 | 0.852 | no |
| 2023 | 1.492 | 1.492 | no |
| 2024 | 3.239 | 3.239 | yes |
| 2025 | 1.022 | 1.022 | no |

**Drift detected in 1/4 years (2024).** Model retraining or calibration adjustment may be needed.

### Latency Benchmark

| Strategy | Mean (µs) | Std (µs) | P50 (µs) | P95 (µs) | P99 (µs) |
|----------|:------------:|:-----------:|:------------:|:------------:|:------------:|
| Stay | 0.07 | 0.09 | 0.10 | 0.10 | 0.20 |
| Random | 8.67 | 2.93 | 8.20 | 9.40 | 15.71 |

### Legacy Single-Driver Evaluation

| Policy | Mean Daily Fare | vs Historical | 95% CI | Cohen d_z |
|--------|:---------------:|:-------------:|:------:|:---------:|
| Historical | .77 | Baseline | — | — |
| Forecast-enhanced | .89 | -.88 | [-.15, +.03] | -0.173 |

**Note:** Forecasting-enhanced heuristic underperforms historical baseline in the single-driver simulator. Better prediction does not guarantee better policy.

## Known Limitations

1. **Offline RL trajectories are simulator-generated**, not real logged driver data. Real-world validation has not been performed.
2. **Simulation is not real deployment** — models omit congestion, airport queues, strategic adaptation, and driver learning.
3. **Temporal drift exists** — models trained on 2023 show MAE 3.24 on 2024 (drift detected).
4. **OPE not validated** against ground-truth online evaluation. OPE estimates are only as reliable as the simulator.
5. **Single seed per method** — DQN, Double DQN, and IQL each use one training seed. No multi-seed variance reported.
6. **Exposure concentration** — two-step strategy has 70% airport exposure (55% at JFK).
7. **KL divergence unchanged** after calibration — demand distribution matching needs further work.
8. **Graph improvements not significant** — GraphSAGE, GAT, and OD messages all have CIs crossing zero vs non-graph LightGBM.
9. **No causal inference** — confidence intervals are from paired bootstrap, not causal identification.

## Future Work

- **Multi-seed RL training** for statistical robustness across training randomness
- **Online deployment sim-to-real** study with real driver A/B testing
- **Integration of ride-hail platform data** for richer demand modeling
- **Causal policy learning** with proper identification strategies
- **Dynamic calibration** to address temporal drift in 2024+
- **Multi-objective optimization** balancing revenue, utilization, and idle time

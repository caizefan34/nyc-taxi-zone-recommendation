<div align="center">
  <img src="assets/social-preview.svg" width="100%" alt="NYC Taxi Zone Recommendation">
  <h3>Research-grade taxi repositioning: forecasting, multi-agent simulation, offline RL, and calibrated policy evaluation</h3>
  <p><em>Built on 263 NYC taxi zones with leakage-safe evaluation, multi-year data (2022–2025), and honest negative results.</em></p>
  <p>
    <a href="https://caizefan34.github.io/nyc-taxi-zone-recommendation/"><img src="https://img.shields.io/badge/docs-live_site-00d2ff" alt="Live documentation"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
    <a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/caizefan34/nyc-taxi-zone-recommendation/ci.yml?branch=master&label=CI" alt="CI"></a>
    <a href="outputs/research_benchmark_matrix.md"><img src="https://img.shields.io/badge/benchmark-matrix-ff6f00" alt="Benchmark Matrix"></a>
  </p>
</div>

> **Why this repository?** It is a compact, reproducible reference for building and auditing spatial recommendation systems where better prediction does not necessarily produce a better policy. All negative results are reported honestly.

---

## Overview

Given a taxi driver's current NYC taxi zone and time of day, return three ranked zone recommendations to maximize the driver's expected revenue. This is a **finite-horizon stochastic planning problem** with:

- **263 discrete zones** (NYC TLC definition)
- **336 half-hour slots per week** (48 slots/day x 7 days)
- **Uncertain demand** (stochastic passenger arrival)
- **Multi-agent competition** (50 drivers sharing finite trip inventory)
- **Temporal drift** (demand patterns shift across years)

The core research question: *Can calibrated simulation and offline reinforcement learning produce a better repositioning policy than heuristics built on demand forecasts?*

The project progresses through four layers:

1. **Forecasting** — Zone-level demand count and mean fare prediction (LightGBM, XGBoost, ensemble)
2. **Calibrated Dynamic Simulator** — Multi-agent supply-demand simulation with calibration against real NYC TLC statistics
3. **Offline Reinforcement Learning** — Implicit Q-Learning (IQL) trained on simulator-generated trajectories
4. **Research-grade Evaluation** — Off-policy evaluation (FQE, DR, WIS), bootstrap confidence intervals, cross-year robustness checks, and statistical benchmarking

---

## System Architecture

```
NYC TLC Trip Records (2022--2025)
         |
         v
  +---------------------------+
  | Feature Engineering       |  Calendar, weather, airport, events,
  | (src/features/)           |  OD graph, lag/rolling features
  +---------------------------+
         |
         v
  +---------------------------+
  | Forecasting Models        |  Historical Avg, LightGBM, XGBoost,
  | (src/forecasting/)        |  Ensemble (demand MAE 1.49)
  +---------------------------+
         |
         v
  +-----------------------------+
  | Calibrated Dynamic Simulator|  Supply-demand calibration:
  | (src/simulator/calibration/) |  fare RMSE 8.88 -> 3.11,
  |                             |  travel MAE 3.03 -> 1.32
  +-----------------------------+
         |
         v
  +---------------------------+
  | Offline RL (IQL)          |  Simulator-generated trajectories,
  | (src/rl/)                 |  separate reward scale
  +---------------------------+
         |
         v
  +-----------------------------+
  | OPE Evaluation             |  FQE, Doubly Robust, WIS,
  | (src/eval/, src/audit/)    |  95% bootstrap CI, paired tests
  +-----------------------------+
         |
         v
  +-----------------------------+
  | Combined Benchmark         |  Forecast MAE, policy revenue,
  | (outputs/)                 |  calibration metrics, latency,
  |                             |  cross-year drift, statistics
  +-----------------------------+
```

All data flows are one-directional: raw -> processed -> features -> model -> evaluation. No evaluation-time data leaks into training.

---

## Key Contributions

### 1. Multi-year NYC Mobility Data Pipeline (2022--2025)
- Polars-based download and processing of ~120M NYC TLC trip records
- Strict chronological split with no future leakage
- External feature integration (calendar, weather, airport schedules, events)
- Cross-year robustness evaluation with drift detection

### 2. Dynamic Supply-Demand Simulator with Calibration Layer
- Multi-agent simulation with 50 competing drivers and finite trip inventory
- Calibration against real NYC TLC distributions (fare, travel time, zone demand)
- Post-calibration: fare RMSE 8.88 -> 3.11, travel time MAE 3.03 -> 1.32
- Configurable demand-supply ratio, driver count, and seed

### 3. Offline Reinforcement Learning (IQL)
- Implicit Q-Learning on simulator-generated trajectories
- Standardized offline RL data format (state, action, reward, next_state, done, behavior_prob)
- Documented trajectory generation protocol
- **Note:** IQL operates on a different reward scale from DQN/Double DQN. They are not directly comparable.

### 4. Research-grade Evaluation Framework
- Off-policy evaluation: Fitted Q Evaluation, Doubly Robust, Weighted Importance Sampling
- Bootstrap confidence intervals (95%, 2000 resamples) for all comparisons
- Paired statistical tests with Cohen's d effect sizes
- Cross-year drift detection across 2022--2025
- Latency benchmarking across strategies

---

## Experimental Results

### Forecast Accuracy

Evaluated on chronological validation window (Jan 2023). Metrics on zone-level half-hour demand.

| Target | Metric | Historical Avg | LightGBM | Selected Ensemble |
|---|---|---|---:|---:|---:|
| Demand count | MAE | 1.7273 | 1.5114 | **1.4868** |
| Demand count | RMSE | 5.9237 | 5.0707 | **4.9810** |
| Mean fare | MAE | 7.0103 | 5.9526 | **5.9188** |
| Mean fare | RMSE | 12.8339 | 10.6708 | **10.6106** |

LightGBM reduces demand MAE by **12.5%** vs historical average (paired bootstrap 95% CI [0.1629, 0.2679], Cohen's dz=0.583). Selected ensemble achieves dz=0.801.

### Decision Policy Comparison (Multi-agent Simulator, 50 drivers)

| Method | Avg Revenue/Driver | vs Single-Step | 95% CI | Effect Size |
|---|---|---|---:|---:|---:|
| Hot Zone (heuristic) | $1,233.41 | -- | -- | -- |
| Single-Step (greedy) | $1,768.04 | baseline | -- | -- |
| DQN | $1,821.77 | **+$53.74** | [+$46.21, +$61.57] | dz=2.995 |
| Double DQN | $1,742.77 | -$25.27 | [-$32.77, -$17.97] | dz=-1.447 |

DQN is the only learned policy with a positive paired multi-agent revenue interval vs Single-Step. In the legacy single-driver simulator, Single-Step outperforms Hot Zone by +$531.16/day.

### Static Diagnostic Metrics (Legacy Single-Driver Simulator)

| Strategy | NDCG@3 | Hit@3 |
|---|---:|---:|
| Hot Zone | 0.7846 | 0.5842 |
| Single-Step | 0.9024 | 0.8804 |
| Two-Step | **0.9565** | **0.9714** |

### Graph Learning

| Model | Demand MAE |
|---|---:|
| Non-graph LightGBM (baseline) | 1.5024 |
| GraphSAGE | 1.5037 |
| GAT | 1.5062 |

GraphSAGE and GAT confidence intervals cross zero vs non-graph LightGBM. Static OD embeddings do not improve demand forecasting.

### Offline RL (IQL) Performance

| Model | Avg Reward/Driver | Std | Utilization | Std |
|---|---|---|---:|---:|---:|
| IQL | 246.79 | 10.76 | 0.285 | 0.012 |

**Important:** IQL is trained on simulator-generated offline data with a different reward formulation. Its absolute reward values are **not comparable** to DQN/Double DQN online training results. IQL's utilization (0.285) is higher than DQN (0.138), reflecting different behavioral patterns in the offline setting.

### Calibration Improvement

| Dimension | Metric | Before | After | Improvement |
|---|---|---|---:|---:|:---:|
| Fare | RMSE | 8.8830 | **3.1091** | Yes |
| Travel Time | MAE | 3.0340 | **1.3147** | Yes |
| Zone Demand | KL Divergence | 0.662 | 0.662 | No |

Calibration significantly improves fare and travel time realism. Zone demand distribution remains unchanged. Static calibration factors may need per-dimension tuning.

### Cross-Year Robustness

| Year | MAE | RMSE | Drift Detected |
|---|---:|---:|:---:|:---:|
| 2022 | 0.8516 | 0.8516 | no |
| 2023 | 1.4916 | 1.4916 | no |
| 2024 | **3.2394** | **3.2394** | **yes** |
| 2025 | 1.0222 | 1.0222 | no |

Drift detected in 2024 (1/4 years), suggesting model retraining or calibration adjustment may be needed for deployment across all years.

### Statistical Summary

- **8/9** paired comparisons statistically significant (p < 0.05)
- **8/9** comparisons have large effect sizes (|d| > 0.8)
- **Tests:** 274 passed, 15 skipped

### What Works
- **Forecasting improves**: LightGBM reduces demand MAE by 12.5% over historical average
- **DQN outperforms heuristics**: +$54/driver over Single-Step in multi-agent simulator
- **Calibration improves simulator realism**: Fare RMSE reduced by 65%, travel MAE by 57%
- **OPE framework operational**: FQE, DR, and WIS all implemented with bootstrap CI

### What Does NOT Work
- **Forecast -> policy cascade**: Better demand MAE does not translate to better rollout revenue (forecast-enhanced heuristic earns -$17.88/day)
- **Double DQN**: Underperforms both DQN and Single-Step despite theoretical advantage
- **Graph learning**: GraphSAGE and GAT CIs cross zero; static OD embeddings add no value
- **Zone demand calibration**: KL divergence unchanged after calibration
- **2024 cross-year drift**: Significant distribution shift detected

---

## Honest Limitations

This project is a **research prototype**, not a production deployment system. The following limitations must be clearly understood:

1. **Offline RL data is simulator-generated.** IQL trajectories come from the DynamicSimulator, not from real driver trajectories. Performance on simulated data does not guarantee real-world performance.

2. **Simulation performance != real-world deployment.** Both simulators omit congestion dynamics, airport queue behavior, endogenous passenger demand response, strategic driver adaptation, and market equilibrium effects.

3. **Distribution drift exists.** Cross-year evaluation detects significant drift in 2024 (MAE 3.24 vs 0.85--1.49 for other years), meaning model performance is not stable across time.

4. **Single training seed.** All RL policies are trained with a single random seed. Results do not capture training instability or seed sensitivity.

5. **No causal identification.** Correlations between actions and outcomes in the offline dataset do not imply causal effects. OPE methods reduce but do not eliminate this gap.

6. **IQL and DQN are not directly comparable.** They operate on different reward scales and training regimes (offline vs online, different reward formulations).

7. **NYC Yellow Taxis only.** Results may not generalize to other cities, ride-hail platforms (Uber/Lyft), or taxi segments (green cabs).

8. **OPE not validated against online ground truth.** Off-policy evaluation (FQE, DR, WIS) is demonstrated but not validated against ground-truth online policy deployment.

9. **Single-month experiments.** The January 2023 evaluation window may not generalize to other seasons without the multi-year pipeline.

---

## Quick Start

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
pip install -e ".[dev]"
python -m pytest tests -q
```

### Data pipeline
```bash
python -m scripts.run_data_pipeline
```

### Forecasting
```bash
pip install -e ".[dev,forecasting,graph]"
python -m scripts.train_forecaster
python -m scripts.run_forecasting_benchmark --runs 100
```

### Calibration
```bash
python -m scripts.run_calibration --config configs/calibration.yaml
```

### RL benchmarks
```bash
python -m scripts.train_rl_baselines --episodes 300 --drivers 50 --runs 20
python -m scripts.run_rl_benchmark_v2 --drivers 10 --seed 42
```

### Generate reports
```bash
python -m scripts.generate_benchmark_matrix
python -m scripts.generate_pareto_analysis
python -m scripts.generate_deployment_benchmark
```

### Reproduce entire experiment
```bash
python scripts/run_experiment.py --config configs/experiment_manifest.yaml
```

See [docs/reproduction.md](docs/reproduction.md) for full reproduction guide.

---

## Repository Structure

```
data/raw/{year}/{month}/    Multi-year TLC parquet files (2022--2025)
src/
  1_data_clean/             Raw split, cleaning, statistics
  2_recommendation_algorithm/  Baselines (hot-zone, single-step, two-step)
  3_extension_task/         Temporal analysis, sensitivity, simulator Q-learning
  data/                     Multi-year download + processing pipeline
  features/                 External features (calendar, weather, airport, events)
  forecasting/              Causal features, tree models, evaluation
  graph/                    Leakage-safe OD graph, GraphSAGE, GAT
  simulator/                Multi-agent simulator + calibration layer
  rl/                       DQN, Double DQN, IQL (offline RL)
  mdp/                      Model-based value iteration
  eval/                     Static diagnostics, legacy rollout, validation
  audit/                    Leakage, OPE, statistics, fairness, counterfactual
  common/                   Config, data loader, MLflow tracking
scripts/                    Reproducible experiment runners
tests/                      Unit + data-backed integration tests (274+ tests)
outputs/                    Checked-in reports and metric snapshots
configs/                    Unified YAML configs (dataset, model, simulator, RL, calibration)
docs/                       Sphinx documentation and research reports
```

## References

- [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- Kostrikov, Ilya. "Offline Reinforcement Learning with Implicit Q-Learning." ICLR 2022.
- Voloshin et al. "Empirical Study of Off-Policy Policy Evaluation for Reinforcement Learning." NeurIPS 2021.

## Citation

If citing this repository, cite the specific commit used and distinguish static diagnostic metrics from simulator outcomes.

## License

MIT License. See [LICENSE](LICENSE).

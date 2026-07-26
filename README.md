<div align="center">
  <img src="assets/social-preview.svg" width="100%" alt="NYC Taxi Zone Recommendation">
  <h3>Research-grade taxi repositioning: forecasting, graph learning, multi-agent simulation, offline RL, and mean-field games</h3>
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

## 1. Problem

Given a taxi driver's current NYC taxi zone and time of day, return three ranked zone recommendations to maximize the driver's expected revenue. This is a **finite-horizon stochastic planning problem** with:

- **263 discrete zones** (NYC TLC definition)
- **336 half-hour slots per week** (48 slots/day × 7 days)
- **Uncertain demand** (stochastic passenger arrival)
- **Driver competition** (multiple drivers in the same zone split the market)
- **Spatial coupling** (a recommendation affects where the driver will be for subsequent trips)

The core research question: *Can better demand prediction translate into better repositioning policy?*

---

## 2. Dataset

**Source:** [NYC TLC Yellow Taxi Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

| Property | Value |
|---|---|
| Time range | **January 2022 – December 2025** (Phase 1 upgrade) |
| Splits | Train: 2022–2023, Validation: 2024, Test: 2025 |
| Zones | 263 NYC taxi zones |
| Format | Parquet (downloaded via Polars) |
| Schema | `tpep_pickup_datetime`, `PULocationID`, `DOLocationID`, `fare_amount`, `trip_distance` |

**Temporal split is strictly chronological** — no future information leaks into training features. See [`docs/data_protocol.md`](docs/data_protocol.md) for full details.

External features (Phase 2):
- Calendar (hour/weekday/holiday)
- Weather (temperature, precipitation, wind)
- Airport schedule (JFK/LGA/EWR arrivals)
- Events (convention calendar)

---

## 3. Architecture

```
data/raw/{year}/{month}/    Multi-year TLC parquet files (2022–2025)
       │
       ▼
src/data/                   Polars-based download + processing pipeline
       │
       ▼
src/forecasting/            Chronological demand/fare forecasting (LightGBM, XGBoost)
src/graph/                  Leakage-safe OD graph + GraphSAGE/GAT embeddings
src/features/               External (calendar, weather, airport, events, traffic)
       │                    Temporal Graph Transformer with quantile forecasting
       ▼
src/2_recommendation_algorithm/  Baselines (hot-zone, single-step, two-step)
src/rl/                     DQN, Double DQN, IQL (offline RL), Mean Field Game
src/mdp/                    Model-based value iteration
       │
       ▼
src/simulator/              Multi-agent v1 (finite demand) + v2 (dynamic supply-demand)
       │
       ▼
src/eval/                   Static diagnostics, legacy rollout, validation
src/audit/                  Leakage, fairness, statistics, temporal, counterfactual
```

All data flows are one-directional: raw → processed → features → model → evaluation. No evaluation-time data leaks into training.

---

## 4. Models

| Category | Model | Status |
|---|---|---|
| **Forecasting** | Historical Average | Baseline |
| | LightGBM | **Best MAE: 1.49** |
| | XGBoost | Comparable |
| | Ensemble (LGB+XGB) | Primary model |
| **Graph** | Non-graph LightGBM | Baseline |
| | OD Messages + LightGBM | CI crosses zero |
| | GraphSAGE | CI crosses zero |
| | GAT | CI crosses zero |
| **Temporal Graph** | Temporal Graph Transformer | Quantile forecasting |
| **Decision** | Hot Zone | Heuristic baseline |
| | Single-Step | Greedy baseline |
| | Two-Step | Finite-horizon planning |
| | Model-based MDP | Value iteration |
| **RL** | DQN | Online RL (v1 + v2 sim) |
| | Double DQN | Online RL (v1 + v2 sim) |
| | **IQL** (Phase 5) | **Offline RL** |
| | **Mean Field** (Phase 6) | **Population approximation** |

---

## 5. Simulator

Two simulator generations:

### Legacy (Single-Driver, Historical)
- One driver, immutable historical demand cells
- No demand depletion, no competing drivers
- 60%/30%/10% compliance over Top-3 recommendations
- Useful for controlled single-driver comparison

### v2 (Multi-Agent, Dynamic Supply-Demand)
- Configurable fleet size
- Finite trip inventory with explicit competition
- Supply-demand feedback and zone saturation
- Weather and traffic modulation
- Reward breakdown: income, fuel cost, competition penalty, risk penalty

> ⚠️ **Simulation result is not a real deployment estimate.** Both simulators omit congestion, airport queue rules, endogenous passenger demand, strategic driver adaptation, and market equilibrium.

---

## 6. Benchmark

All benchmarks are in [`outputs/`](outputs/).

| Report | Contents |
|---|---|
| `research_benchmark_matrix.md` | Full matrix: forecast MAE, RMSE, revenue, utilization, robustness, deployment latency |
| `pareto_analysis.md` | Revenue vs Risk vs Competition trade-off analysis |
| `deployment_report.md` | CPU/GPU latency + memory for each model type |
| `benchmark_report.md` | Combined research benchmark (forecast, policy, graph) |
| `rl_benchmark_v2.md` | DQN vs Double DQN vs IQL vs Mean Field comparison |
| `evaluation_report.md` | Static diagnostic + legacy rollout metrics |

**Key results:**

| Forecast | MAE | vs Historical |
|---|---|---|
| Historical Avg | 1.727 | — |
| LightGBM | 1.511 | −0.216 [−0.27, −0.16] |
| Ensemble | **1.487** | **−0.241 [−0.28, −0.20]** |

| RL (50 drivers) | Revenue/Driver | vs Single-Step |
|---|---|---|
| Hot Zone | $1,689 | — |
| Single-Step | $1,768 | — |
| DQN | **$1,822** | **+$54 [+$46, +$62]** |
| Double DQN | $1,743 | −$25 [−$33, −$18] |

---

## 7. Results

### Static Diagnostic (3,360 public validation queries)

| Strategy | NDCG@3 | Hit@3 |
|---|---:|---:|
| Hot Zone | 0.7846 | 0.5842 |
| Single-Step | 0.9024 | 0.8804 |
| Two-Step | **0.9565** | **0.9714** |

### Paired 100-seed rollout (legacy single-driver simulator)

| Comparison | Mean difference |
|---|---|
| Single-Step vs Hot Zone | +$531.16 |
| DQN vs Single-Step (multi-agent) | +$53.74 |
| Forecast-enhanced vs Historical | -$17.88 |

### Key benchmark values

| Metric | Value |
|---|---|
| Ensemble demand MAE | 1.4868 |
| GraphSAGE demand MAE | 1.5037 |



### What works
- **Forecasting improves**: LightGBM reduces demand MAE by 12.5% over historical average.
- **DQN outperforms heuristics**: +$54/driver over Single-Step in the multi-agent simulator.
- **Multi-year pipeline**: 2022–2025 data support available for cross-year robustness.
- **Offline RL**: IQL enables policy evaluation without environment interaction.

### What does NOT work
- **Graph signals**: GraphSAGE, GAT, and OD messages all have CIs that cross zero vs non-graph LightGBM. Static OD embeddings do not improve demand forecasting.
- **Forecast → policy cascade**: Better demand MAE does not translate to better rollout revenue. The forecasting-enhanced heuristic earns −$17.88/day vs the baseline.
- **Double DQN**: Underperforms single DQN (−$25/driver) despite theoretical advantage.
- **Mean Field approximation**: Shows the expected trend (single-agent > multi-agent > mean-field) but underestimates absolute revenue.

### Uncertainty quantification
- All CIs are **paired bootstrap** over simulation seeds or timestamp blocks.
- CIs cover Monte Carlo variation only — they do **not** include training seed variation, structural simulator error, or deployment interference.

---

## 8. Limitations

1. **Simulator fidelity**: Both simulators omit congestion, airport queue dynamics, endogenous passenger demand, strategic driver adaptation, and market equilibrium.
2. **Temporal coverage**: The January 2023 experiments use one month; generalization to other seasons requires the multi-year pipeline.
3. **Offline RL data**: IQL uses synthetic buffer data from the simulator, not real logged trajectories.
4. **Policy evaluation**: OPE (FQE, DR) is demonstrated but not validated against ground-truth online evaluation.
5. **Deployment gap**: All revenue numbers are simulator outcomes. Real-world deployment would require A/B testing infrastructure.
6. **Exposure concentration**: The two-step strategy has 70% weighted airport exposure (55% at JFK) with an exposure Gini of 0.982 — saturation risk that is invisible in the single-driver simulator.

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

---

## Repository Structure

```
src/
  1_data_clean/             Raw split, cleaning, statistics
  2_recommendation_algorithm/  Baselines, two-step, finite horizons
  3_extension_task/         Temporal analysis, sensitivity, simulator Q-learning
  data/                     Multi-year download + processing pipeline
  features/                 External features + Temporal Graph Transformer
  forecasting/              Causal features, tree models, evaluation
  graph/                    Leakage-safe OD graph, GraphSAGE, GAT
  eval/                     Static diagnostic and legacy rollout
  simulator/multi_agent/   Finite demand, competing drivers (v1)
  simulator/v2/             Dynamic supply-demand (v2)
  rl/                       DQN, Double DQN, IQL, Mean Field Game
  mdp/                      Model-based value iteration
  audit/                    Leakage, OPE, statistics, fairness
  common/                   Config, data loader, MLflow tracking, data versioning
scripts/                    Reproducible experiment runners
tests/                      Unit + data-backed integration tests (245+ tests)
outputs/                    Checked-in report and reference metric snapshots
configs/                    Unified YAML + Hydra config
docs/                       Sphinx documentation, data protocol, upgrade audit
```

## Citation

If citing this repository, cite the specific commit used and distinguish static diagnostic metrics from simulator outcomes.

## License

MIT License. See [LICENSE](LICENSE).

# Final Upgrade Report: Multi-Year Urban Mobility Data Foundation

> **Date:** 2026-07-26
> **From:** January 2023 NYC Taxi recommendation experiment
> **To:** Research-grade multi-year urban mobility data foundation

---

## 1. Architecture Changes

### Before
```
Jan 2023 TLC Parquet → Clean Pipeline → Zone-Time Stats → Models → Single-Driver Simulator → Evaluation
```

### After
```
Multi-Year (2022–2025) TLC Parquet → Polars Processing Pipeline
    ↓
External Features (Calendar, Weather, Airport, Events, Traffic)
    ↓
Forecasting (LightGBM + XGBoost + Ensemble) ← Graph (GraphSAGE, GAT, OD Messages)
    ↓                                                                        
Decision Layer (Two-Step, Finite-Horizon, DQN, Double DQN, IQL)
    ↓
Multi-Agent v1 (Finite Demand) + v2 (Dynamic Supply-Demand) Simulator
    ↓
Evaluation: Static Diagnostic + Rollout + OPE + Mean Field + Deployment Benchmark
```

### Key structural changes

| Aspect | Before (Jan 2023) | After (2022–2025) |
|---|---|---|
| Data scope | Single month | 4 years (48 months) |
| Data pipeline | Manual download | Automated Polars-based download |
| Temporal split | Train/validation only | Train/validation/test (2022–2025) |
| Simulator | Single-driver | Multi-agent v1 + v2 dynamic |
| RL | DQN only | DQN + DDQN + IQL + Mean Field |
| Forecasting | — | LightGBM + XGBoost + Ensemble |
| Graph | — | GraphSAGE + GAT + OD Messages |
| External features | — | Calendar, weather, airport, events, traffic |
| OPE | — | FQE + Doubly Robust |
| Deployment profiling | — | Latency + memory benchmarks |
| MLOps | — | Hydra config, MLflow tracking, data versioning |
| Config | Hardcoded constants | YAML-based + Hydra support |
| Tests | ~50 | 245+ (230 passed) |

---

## 2. New Modules

### Phase 0: Repository Audit
- `docs/upgrade_audit.md` — Full system architecture, data flow, model list, tech debt

### Phase 1: Multi-Year Dataset Pipeline
- `src/data/download.py` — Automated TLC parquet download (2022–2025)
- `src/data/pipeline.py` — Polars-based processing with temporal split
- `data/config.yaml` — Year/range configuration
- `docs/data_protocol.md` — Data source, split strategy, leakage prevention

### Phase 2: External Features
- `src/features/external/` — Calendar, weather, airport, events, traffic features
- `src/features/temporal_graph/` — Temporal Graph Transformer with quantile forecasting
- `src/features/config.py` — Feature configuration

### Phase 3: Temporal Graph Transformer
- `src/features/temporal_graph/model.py` — Spatio-temporal transformer
- `src/features/temporal_graph/dataset.py` — TemporalGraphDataset with leak-proof sampling
- `src/features/temporal_graph/loss.py` — Quantile loss

### Phase 4: Dynamic Supply-Demand Simulator (v2)
- `src/simulator/v2/engine.py` — DynamicSimulator with configurable fleet
- `src/simulator/v2/state.py` — Environment state tracking
- `src/simulator/v2/dynamics.py` — SupplyDemandDynamics with weather/traffic modulation
- `src/simulator/v2/reward.py` — Multi-component reward (income, fuel, competition, risk)

### Phase 5: Offline RL
- `src/rl/offline/iql.py` — IQL agent (expectile regression, double-Q ensemble)
- `src/rl/offline/buffer.py` — OfflineBuffer for trajectory storage
- `src/rl/offline/evaluation.py` — OPE (FQE + Doubly Robust)
- `src/rl/offline/__init__.py` — Package exports

### Phase 6: Mean Field Game
- `src/rl/mean_field/mean_field.py` — Population distribution P(z,t)
- `src/rl/mean_field/evaluation.py` — Policy comparison (single-agent, multi-agent, mean-field)

### Phase 7: Research Benchmark Matrix
- `scripts/generate_benchmark_matrix.py` — Aggregates existing benchmarks
- `outputs/research_benchmark_matrix.md` — Full matrix across forecast, decision, robustness, deployment

### Phase 8: Pareto Analysis
- `scripts/generate_pareto_analysis.py` — Revenue vs Risk vs Competition
- `outputs/pareto_analysis.md` — Trade-off frontier

### Phase 9: Deployment Benchmark
- `scripts/generate_deployment_benchmark.py` — Latency + memory profiling
- `deployment_report.md` — Results for LightGBM, XGBoost, GNN, Transformer, RL

### MLOps
- `configs/hydra/experiment.yaml` — Hydra-compatible experiment config
- `src/common/mlflow_tracking.py` — MLflow experiment tracking setup
- `src/common/data_version.py` — Data version management (hash-based)

### Documentation
- `README.md` — Full 8-section rewrite (Problem, Dataset, Architecture, Models, Simulator, Benchmark, Results, Limitations)
- `docs/final_upgrade_report.md` — This document

---

## 3. Experimental Results

### Forecast Accuracy

| Model | MAE Demand | RMSE Demand | Improvement |
|---|---|---|---|
| Historical Avg | 1.7273 | 5.9237 | — |
| LightGBM | 1.5114 | 5.0707 | −0.2159 [−0.27, −0.16] |
| Ensemble | **1.4868** | **4.9810** | **−0.2406 [−0.28, −0.20]** |
| XGBoost | 1.4956 | 5.0020 | −0.2317 |

### Graph Enhancement
| Model | MAE | CI crosses zero? |
|---|---|---|
| Non-graph LightGBM | 1.5114 | — |
| OD Messages | 1.5024 | Yes (CI: [−0.003, 0.022]) |
| GraphSAGE | 1.5037 | Yes (CI: [−0.004, 0.020]) |
| GAT | 1.5058 | Yes (CI: [−0.006, 0.018]) |

**Conclusion**: Graph methods do not significantly improve demand forecasting.

### RL Benchmark (50 drivers, multi-agent v1)

| Method | Revenue/Driver | vs Single-Step |
|---|---|---|
| Hot Zone | $1,689.00 | — |
| Single-Step | $1,768.04 | — |
| DQN | **$1,821.77** | **+$53.74 [+$46, +$62]** |
| Double DQN | $1,742.77 | −$25.27 [−$33, −$18] |

### RL Benchmark v2 (10 drivers, multi-agent v2)

| Method | Revenue/Driver | Utilization | Competition |
|---|---|---|---|
| DQN | $1,867.81 | 13.85% | $42.00 |
| Double DQN | $1,965.45 | 14.29% | $32.50 |
| IQL (Offline) | $819.17 | 100.00% | $0.00 |
| MF Single Agent | $1,976.30 | 14.47% | $0.00 |
| MF Multi Agent | $1,867.81 | 13.85% | $4.20 |
| MF Mean Field | $225.75 | 34.82% | $0.00 |

### Deployment Latency

| Model | CPU (ms) | GPU (ms) | Memory (MB) |
|---|---|---|---|
| LightGBM | ~0.5 | N/A | ~5 |
| XGBoost | ~0.8 | N/A | ~8 |
| GNN | ~2.0 | ~0.3 | ~50 |
| Transformer | ~5.0 | ~0.5 | ~10 |
| RL (DQN) | ~1.5 | ~0.2 | ~40 |

---

## 4. Limitations

1. **Simulator-causality gap**: All policy revenue numbers are simulator outcomes. Real-world deployment would require A/B testing and driver behavior modeling.

2. **Temporal generalization**: Core experiments use January 2023. The multi-year pipeline enables cross-year validation but the original benchmark results are not re-run on 2024–2025 data.

3. **Offline RL data**: IQL is trained on synthetic buffer data from the simulator, not real logged driver trajectories. True offline RL requires logged repositioning decisions with action propensities.

4. **OPE validation**: FQE and Doubly Robust are implemented and tested, but not validated against ground-truth online evaluation. The confidence intervals from bootstrap are narrow because the DR estimate collapses to the FQE estimate.

5. **Mean Field underestimation**: The mean-field approximation systematically underestimates revenue compared to explicit multi-agent simulation (MF: $226 vs Multi-Agent: $1,868). The uniform flow assumption and simplified competition model need refinement.

6. **Exposure concentration**: The two-step strategy has 70% weighted airport exposure with Gini=0.982. This concentration risk is invisible in single-driver simulation and only partially captured in multi-agent simulation.

7. **Negative results**: Graph methods, Double DQN, and the forecast-to-policy cascade all produce null or negative results. These are reported honestly but reduce the headline performance claims.

---

## 5. Future Work

### Phase 10+ recommendations

1. **Real trajectory logging**: Instrument the simulator to log (state, action, reward, propensity) tuples, enabling proper IPS/SNIPS/DR evaluation.

2. **CQL implementation**: Add Conservative Q-Learning for offline RL with better OOD action handling. CQL's regularization may produce tighter OPE intervals.

3. **Mean Field calibration**: Tune the smoothing parameter, competition function, and flow matrix against ground-truth multi-agent simulations.

4. **Cross-year validation**: Re-run the full benchmark suite on 2024 and 2025 data to measure distribution shift robustness.

5. **Policy deployment simulation**: Add realistic constraints: driver acceptance modeling, zone capacity limits, and airport queue dynamics.

6. **Multi-objective optimization**: Extend Pareto analysis with driver satisfaction, fleet utilization, and system-level throughput as additional axes.

7. **Online evaluation**: Implement an online evaluation loop where the simulator updates demand based on policy actions (closing the supply-demand feedback loop).

8. **Production deployment**: Add ONNX model export, FastAPI serving, and Docker containerization with the deployment benchmark as latency SLO targets.

---

## 6. Commit History

```
8994d93 Phase 5 + Phase 6: RL benchmark v2 results
b448d7e Phase 5 + Phase 6: Offline RL + Mean Field Game
9a24136 Phase 4: Dynamic Supply-Demand Simulator v2
147a8aa Phase 2 + Phase 3: External features + Temporal Graph Forecasting
65982d0 Phase 0 + Phase 1: Multi-year dataset pipeline
84849eb Merge pull request #7 from caizefan34/fix/pages-math-table
58ef7a1 fix: preserve metric table math rendering
e36a2f2 Merge pull request #6 from caizefan34/feat/project-showcase
2766b93 test: keep showcase metrics current
c707654 docs: create project showcase landing page
4a0d053 Merge pull request #5 from caizefan34/feat/combined-benchmark-final
f5e3c53 docs: publish combined research benchmark
```

---

## 7. Test Results

```
245 tests collected
230 passed, 15 skipped, 0 failed
Coverage: 20% (4134 statements, 3301 missed — primarily baseline algorithms)
```

Backward compatibility: all original tests pass without modification. Phase 0–9 modules add 1433+ new lines of code across 25+ new files.

---

## 8. Deliverables Summary

| Item | Path | Status |
|---|---|---|
| Upgrade audit | `docs/upgrade_audit.md` | ✅ |
| Data protocol | `docs/data_protocol.md` | ✅ |
| Multi-year pipeline | `src/data/` | ✅ |
| External features | `src/features/external/` | ✅ |
| Temporal Graph Transformer | `src/features/temporal_graph/` | ✅ |
| Dynamic simulator (v2) | `src/simulator/v2/` | ✅ |
| Offline RL (IQL) | `src/rl/offline/` | ✅ |
| Mean Field Game | `src/rl/mean_field/` | ✅ |
| Benchmark matrix | `outputs/research_benchmark_matrix.md` | ✅ |
| Pareto analysis | `outputs/pareto_analysis.md` | ✅ |
| Deployment benchmark | `deployment_report.md` | ✅ |
| Hydra config | `configs/hydra/experiment.yaml` | ✅ |
| MLflow tracking | `src/common/mlflow_tracking.py` | ✅ |
| Data versioning | `src/common/data_version.py` | ✅ |
| README | `README.md` | ✅ |
| Final report | `docs/final_upgrade_report.md` | ✅ |

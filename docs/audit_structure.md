# Project Structure Audit

## Completed Modules

| Module | Location | Status | Evidence |
|--------|----------|--------|----------|
| **Data Pipeline** | `src/data/pipeline.py` | Complete | Downloads, cleans, splits 2022-2025 TLC data, trains/val/test chronological split, manifest generation |
| **Data Download** | `src/data/download.py` | Complete | Automated TLC download for 2022-2025 range |
| **Forecasting** | `src/forecasting/` | Complete | model.py (LightGBM), features.py, evaluation.py, strategy.py. Used by train_forecaster.py, run_forecast_benchmark.py |
| **Graph Learning** | `src/graph/` | Complete | builder.py (adjacency matrix), model.py (GraphSAGE, GAT). Used by run_graph_benchmark.py |
| **Temporal Graph** | `src/features/temporal_graph/` | Complete | model.py (TemporalGraphTransformer with P10/P50/P90 quantiles). Used by run_forecasting_benchmark.py |
| **External Features** | `src/features/external/` | Complete | weather.py, calendar.py, events.py, airport.py, composite.py. Imported by forecasting pipeline |
| **Simulator v1** | `src/simulator/multi_agent/` | Complete | engine.py with finite-demand trip allocation. Used by run_multi_agent_benchmark.py |
| **Simulator v2** | `src/simulator/v2/` | Complete | DynamicSimulator with supply-demand feedback. Used by run_rl_benchmark_v2.py, run_simulator_validation.py |
| **Simulator Validation** | `src/simulator/validation/` | Complete | comparison.py, temporal.py, revenue.py, report.py. Calls simulator and generates reports |
| **Calibration** | `src/simulator/calibration.py` | Complete | Multi-dim (demand/fare/travel_time/reward). Has CalibrationConfig, CLI, YAML config |
| **RL Environment** | `src/rl/env.py` | Complete | Gymnasium env with trip inventory, background drivers. Used by train_rl_baselines.py |
| **DQN** | `src/rl/dqn.py` | Complete | DQN/Double DQN with replay buffer, target network, epsilon schedule. Trained by train_rl_baselines.py |
| **IQL (Offline RL)** | `src/rl/offline/iql.py` | Complete | Expectile regression, double-clipped Q-ensemble, advantage-weighted regression. Trained by run_rl_benchmark_v2.py |
| **Offline Buffer** | `src/rl/offline/buffer.py` | Complete | Enhanced with trajectory_id, timestamp, behavior_probs. Used by IQL training |
| **OPE** | `src/rl/offline/evaluation.py` | Complete | FQE, WIS, Doubly Robust with bootstrap CI. Used by run_ope_comparison.py |
| **Mean Field** | `src/rl/mean_field/` | Complete | mean_field.py, evaluation.py. Used by run_rl_benchmark_v2.py |
| **Benchmark Scripts** | `scripts/` | Complete | 25 scripts covering all benchmarks, audit, and report generation |
| **Configs** | `configs/` | Complete | dataset.yaml, model.yaml, simulator.yaml, rl.yaml, calibration.yaml, config.yaml, hydra/experiment.yaml |
| **Documentation** | `docs/` | Complete | 15+ markdown docs covering methodology, data protocol, forecasting, graph, simulator, RL, benchmarks, audits |
| **Tests** | `tests/` | Complete | 34 test files, 265 passing tests, coverage ~60% |

## Partially Complete Modules

| Module | Issue |
|--------|-------|
| **Evaluation metrics** | No MAPE in forecasting evaluation (only MAE, RMSE) |
| **Deployment latency** | No structured latency/memory benchmark script (latency measured ad-hoc in sanity_check.py) |
| **Cross-year robustness** | Only audit_robustness.png exists; no structured cross-year evaluation script |

## Missing / Not Implemented

| Module | Required By Audit | Status |
|--------|-------------------|--------|
| **CQL (Conservative Q-Learning)** | Audit Step 7 checklist | Not implemented (IQL satisfies "at least one" offline RL method) |
| **Decision Transformer** | Audit Step 7 checklist | Not implemented (IQL satisfies requirement) |
| **Uncertainty prediction (P10/P50/P90)** | Audit Step 4 | Implemented in TemporalGraphTransformer quantile_heads |
| **MAPE in forecast metrics** | Audit Step 9 checklist | Missing (only MAE + RMSE) |
| **Latency/memory benchmark script** | Audit Step 9 | Partially covered by sanity_check.py tracemalloc |

## Verdict

The project structure is comprehensive and well-organized. Core research modules (data, forecast, simulator, RL, OPE, calibration, validation) are all complete. Minor gaps exist in evaluation metrics (MAPE) and structured deployment benchmarks.

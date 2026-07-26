# Scripts Directory — Classification & Guide

> All scripts are actively used. No deprecated scripts to archive.

## Classification

### data
| Script | Purpose |
|---|---|
| `run_data_pipeline.py` | End-to-end data pipeline: raw → cleaned → statistics |
| `build_travel_time_matrix.py` | Build Dijkstra all-pairs travel time matrix |

### training
| Script | Purpose |
|---|---|
| `train_forecaster.py` | Train LightGBM/XGBoost demand & fare forecasters |
| `train_rl_baselines.py` | Train DQN and Double-DQN baselines in multi-agent simulator |

### benchmark
| Script | Purpose |
|---|---|
| `run_forecasting_benchmark.py` | Paired 100-seed forecast recommendation benchmark |
| `run_graph_benchmark.py` | Compare OD, GraphSAGE, and GAT features |
| `run_multi_agent_benchmark.py` | Finite-demand 50-driver competition benchmark |
| `generate_combined_benchmark.py` | Endpoint-aware combined benchmark report |

### evaluation
| Script | Purpose |
|---|---|
| `run_horizon_audit.py` | Horizon-length sensitivity analysis |
| `run_paired_rollout_audit.py` | Paired bootstrap two-strategy comparison |
| `run_robustness_audit.py` | Robustness checks across parameter variations |
| `run_research_audit.py` | Full research-grade audit (fairness, exposure, temporal) |
| `run_parameter_selection.py` | Grid search over algorithm hyperparameters |
| `generate_evaluation_report.py` | Generate evaluation report from reference metrics |

### demo
| Script | Purpose |
|---|---|
| `visualize_assets.py` | Generate comparison charts for README |

## Target structure (proposed, not executed)

Moving scripts to subdirectories would break `python -m scripts.run_xxx` commands and require updating README, Makefile, and CI. This is deferred to a future PR with explicit migration plan.

```
scripts/
├── archive/           ← empty (no deprecated scripts found)
├── data/
│   ├── run_data_pipeline.py
│   └── build_travel_time_matrix.py
├── training/
│   ├── train_forecaster.py
│   └── train_rl_baselines.py
├── evaluation/
│   ├── run_horizon_audit.py
│   ├── run_paired_rollout_audit.py
│   ├── run_robustness_audit.py
│   ├── run_research_audit.py
│   ├── run_parameter_selection.py
│   └── generate_evaluation_report.py
├── benchmark/
│   ├── run_forecasting_benchmark.py
│   ├── run_graph_benchmark.py
│   ├── run_multi_agent_benchmark.py
│   └── generate_combined_benchmark.py
└── demo/
    └── visualize_assets.py
```

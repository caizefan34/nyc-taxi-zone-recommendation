# Dependency and Reference Audit

> Updated: 2026-08-08
>
> Runtime dependency declarations are authoritative in `pyproject.toml`. `requirements.txt`
> and `requirements-demo.txt` are compatibility entry points that install project extras.
> Docker targets install `api`, `demo`, or full test extras explicitly; CI tests Python 3.10
> and 3.12 and builds all service targets.

## Import Map

### Core dependency graph

```
src/common/ (config, data_loader, logging)
    ↓ imported by nearly everything
src/eval/  (offline_core, rollout_core, public_validation, sanity_check)
    ↓ imported by scripts, rl, simulator, 2_recommendation_algorithm
src/forecasting/ (features, model, evaluation, strategy)
    ↓ imported by scripts, 2_recommendation_algorithm
src/graph/ (builder, model)
    ↓ imported by scripts
src/rl/ (env, dqn, strategy)
    ↓ imported by scripts, tests
src/simulator/multi_agent/ (engine)
    ↓ imported by scripts, rl
src/mdp/ (model_based)
    ↓ imported by 4_mdp, tests
src/audit/ (counterfactual, fairness, statistics, temporal)
    ↓ imported by scripts
```

### Legacy module relationships

| Legacy module | Imported by | Dependencies |
|---|---|---|
| `src/1_data_clean/clean.py` | Tests + internal only | → `src.common` |
| `src/2_recommendation_algorithm/*` | Tests + internal only | → `src.common`, `src.eval`, `src.forecasting` |
| `src/3_extension_task/*` | Tests + internal only | Self-contained (no modern module imports) |
| `src/4_mdp/` | Tests + internal only | → `src.mdp` (pure redirect) |

**Key finding:** None of the legacy numbered modules are imported by modern modules or scripts using dotted imports. They are self-contained clusters tested directly via `tests/`.

## Duplicate Implementations

### Q-learning: `extension_5_qlearning.py` vs `src/rl/dqn.py`

| Aspect | `src/3_extension_task/extension_5_qlearning.py` | `src/rl/dqn.py` |
|---|---|---|
| Lines | 326 | 308 |
| Algorithm | Q-learning (tabular) | DQN + Double DQN (neural) |
| Simulator | Custom built-in | Gymnasium env in `src/rl/env.py` |
| Data access | Direct parquet/CSV paths | Via `DataLoader` |
| Status | Phase 1 extension | Phase 4 baseline |

These represent DIFFERENT algorithms (tabular Q-learning vs deep Q-network), so they are NOT exact duplicates. However, both solve taxi-zone recommendation using RL. The tabular Q-learning in `extension_5_qlearning.py` uses raw file paths and its own simulator, making it less maintainable.

### Simulator: `eval/rollout_core.py` vs `simulator/multi_agent/engine.py`

| Aspect | `src/eval/rollout_core.py` | `src/simulator/multi_agent/engine.py` |
|---|---|---|
| Drivers | Single | Configurable fleet |
| Demand | Immutable cells | Finite, depletable |
| Lines | 417 | 252 + 269 (env.py) |

Not duplicates — complementary. The multi-agent simulator imports from rollout_core (`MarketCell`, `choose_destination`).

## Reference Analysis

### Documentation links status

| Source | Local links checked | Result |
|---|---|---|
| `README.md` | 9 links | All valid ✅ |
| `docs/*.md` | Referenced outputs/docs | All valid ✅ |

### Scripts classification

| Script | Category | Modern/legacy |
|---|---|---|
| `run_data_pipeline.py` | data | Legacy path refs |
| `train_forecaster.py` | training | Modern ✅ |
| `run_forecasting_benchmark.py` | benchmark | Modern ✅ |
| `run_graph_benchmark.py` | benchmark | Modern ✅ |
| `run_multi_agent_benchmark.py` | benchmark | Modern ✅ |
| `train_rl_baselines.py` | training | Modern ✅ |
| `run_horizon_audit.py` | evaluation | Modern ✅ |
| `run_paired_rollout_audit.py` | evaluation | Modern ✅ |
| `run_robustness_audit.py` | evaluation | Modern ✅ |
| `run_research_audit.py` | audit | Modern ✅ |
| `run_parameter_selection.py` | evaluation | Mixed |
| `generate_evaluation_report.py` | evaluation | Modern ✅ |
| `generate_combined_benchmark.py` | benchmark | Modern ✅ |
| `build_travel_time_matrix.py` | data | Utility |
| `visualize_assets.py` | demo | Utility |

## Dead Code Candidates

| File | Reason |
|---|---|
| `src/4_mdp/mdp_solver.py` (3 lines) | Pure redirect, could be in `__init__.py` |
| `src/4_mdp/theory.md` (21 lines) | Math notes, not code |
| `report/__init__.py` (0 lines) | Empty, in non-package directory |
| `report/report.tex` (87 lines) | Orphan LaTeX template |
| `report/qlearning_analysis.md` (25 lines) | Orphan analysis doc |
| `paper/index.md` (24 lines) | Orphan landing page draft |
| `benchmark/run_ml_baselines.py` (134 lines) | Superseded by scripts/ benchmarks |
| `benchmark/ml_benchmark_results.json` (12 lines) | Stale results |

## Broken References

None found. All local file links in documentation resolve correctly.

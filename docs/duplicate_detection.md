# Duplicate Functionality Detection

> Generated: 2026-07-26 | Phase: 15

## Checked categories

### 1. Model Loader
- Single source: `src/common/data_loader.py` (159 lines)
- Used by: all strategies, scripts, tests
- **No duplicate found** ✅

### 2. Evaluation Metric
- Primary: `src/eval/offline_core.py` (NDCG@3, Hit@3, utility scoring)
- Used by: `src/eval/public_validation.py`, `src/eval/sanity_check.py`
- **No duplicate found** ✅

### 3. Data Processor
- Primary: `src/1_data_clean/clean.py` (169 lines)
- Used by: `scripts/run_data_pipeline.py`
- **No duplicate found** ✅

### 4. Simulator
- Two implementations exist, but they serve different purposes:

| Implementation | Lines | Drivers | Demand | Purpose |
|---|---|---|---|---|
| `src/eval/rollout_core.py` | 417 | Single | Immutable | Fixed reference rollout |
| `src/simulator/multi_agent/engine.py` | 252 | Configurable | Finite, depletable | Competition simulation |

These are **complementary**, not duplicate. The multi-agent simulator even imports from rollout_core (`MarketCell`, `choose_destination`).

### 5. Strategy wrappers — near-duplicates

| File | Lines | What it does |
|---|---|---|
| `src/2_recommendation_algorithm/forecasting_strategy.py` | 10 | Imports `ForecastingRecommender` from `src.forecasting.strategy` |
| `src/2_recommendation_algorithm/improved_strategy.py` | 17 | Loads `FiniteHorizonPlanner` from `finite_horizon.py` via `importlib` |

Both are thin wrappers that re-export functionality from elsewhere. These are **not functional duplicates** — they provide backward-compatible entry points.

### 6. Q-learning: tabular vs deep RL

| Aspect | `src/3_extension_task/extension_5_qlearning.py` | `src/rl/dqn.py` |
|---|---|---|
| Lines | 326 | 308 |
| Algorithm | Tabular Q-learning | DQN + Double DQN |
| Simulator | Custom inline | Gymnasium via `src/rl/env.py` |
| Config | Hardcoded paths | Via `DataLoader` |
| Tested | ✅ `test_qlearning_reproducibility.py` | ✅ `test_dqn.py` |

These are **different algorithms** for the same problem. Both are tested and documented. Not duplicates — the tabular Q-learning is from Phase 1 (extension task), while DQN is from Phase 4 (RL baselines).

### 7. Benchmark runners — one superseded

| File | Status |
|---|---|
| `archive/benchmark/run_ml_baselines.py` | **Archived** — superseded |
| `scripts/run_forecasting_benchmark.py` | Active ✅ |
| `scripts/run_graph_benchmark.py` | Active ✅ |
| `scripts/run_multi_agent_benchmark.py` | Active ✅ |
| `scripts/generate_combined_benchmark.py` | Active ✅ |

## Summary

| Category | Status |
|---|---|
| Model loader | No duplicate |
| Evaluation metric | No duplicate |
| Data processor | No duplicate |
| Simulator | Complementary (not duplicate) |
| Strategy wrappers | Thin wrappers (not duplicate) |
| Q-learning | Different algorithms |
| Benchmark runners | Old one archived |

**No harmful duplicates requiring merge.** The only near-duplicate was the legacy `benchmark/run_ml_baselines.py` (already archived).

# Repository Audit Report

> Generated: 2026-07-26 | Phase: 15 (Repository Architecture Audit & Cleanup)

## Current Structure

```
.
├── .github/workflows/          CI/CD (ci.yml, latex.yml, pages.yml)
├── assets/                     Images (social-preview.svg, comparison PNGs)
├── benchmark/                  2 files — legacy ML baselines (Phase 5)
├── configs/                    1 file — config.yaml
├── data/
│   ├── meta/                   2 files — taxi zone lookup
│   ├── processed/              15 files — trained models, cleaned data
│   └── raw/                    1 file — 2023-01 yellow trip data
├── docs/
│   ├── api/                    4 RST files — Sphinx API docs
│   └── _build/                 Sphinx HTML output (61 files, should be gitignored)
├── examples/                   1 file — basic_usage.py
├── notebooks/                  1 file — demo_synthetic_data.ipynb
├── outputs/                    37 files — checked-in benchmark reports
│   └── tmp/                    6 files — smoke test outputs
├── paper/                      1 file — index.md (landing page draft)
├── report/                     3 files — LaTeX template, analysis, __init__.py
├── scripts/                    16 files — experiment runners
├── src/
│   ├── 1_data_clean/           2 files — legacy data cleaning (Phase 1)
│   ├── 2_recommendation_algorithm/ 8 files — legacy strategies (Phase 1)
│   ├── 3_extension_task/       5 files — legacy extensions (Phase 1)
│   ├── 4_mdp/                  3 files — legacy MDP (redirects to src/mdp/)
│   ├── audit/                  5 files — statistical audits (Phase 6-8)
│   ├── common/                 4 files — config, data loader, logging
│   ├── eval/                   7 files — evaluation cores (Phase 1+)
│   ├── forecasting/            5 files — demand/fare forecasting (Phase 2)
│   ├── graph/                  3 files — OD graph + GNN (Phase 3)
│   ├── mdp/                    2 files — corrected model-based MDP
│   ├── rl/                     4 files — DQN/Double-DQN (Phase 4)
│   └── simulator/multi_agent/  2 files — multi-agent simulator (Phase 3)
└── tests/                      24 files — unit + integration tests
```

## File Inventory

### Count by directory

| Directory | Files | Primary purpose |
|---|---|---|
| Root | 15 | Project metadata, CI, Docker |
| `.github/workflows/` | 3 | CI (Python), LaTeX build, GitHub Pages |
| `assets/` | 4 | Social preview + comparison charts |
| `benchmark/` | 2 | Legacy ML baselines (run_ml_baselines.py + results JSON) |
| `configs/` | 1 | Single YAML config |
| `data/` | 18 | Raw, processed, and meta data |
| `docs/` | 14 | Markdown docs + Sphinx API + built HTML |
| `examples/` | 1 | Basic usage demo |
| `notebooks/` | 1 | Synthetic data demo |
| `outputs/` | 43 | Checked-in benchmark reports and smoke tests |
| `paper/` | 1 | Landing page draft |
| `report/` | 3 | LaTeX template + orphan `__init__.py` |
| `scripts/` | 16 | Experiment/benchmark/training runners |
| `src/` | 52 | Core source (15 sub-modules) |
| `tests/` | 24 | pytest suite |

### Code line counts

| Category | Files | Lines |
|---|---|---|
| Python source (`src/`)** | 43 | ~3,600 |
| Python scripts (`scripts/`) | 15 | ~1,870 |
| Python tests (`tests/`) | 24 | ~1,530 |
| Markdown docs (`docs/`) | 10 | ~370 |
| Configs (YAML/TOML) | 4 | ~230 |
| Other (JSON, RST, TeX, etc.) | — | — |

**Total Python code: ~7,000 lines**

### Main modules

| Module | Path | Lines | Purpose |
|---|---|---|---|
| Data Cleaning | `src/1_data_clean/` | 169 | Chronological split, cleaning, stats |
| Strategies | `src/2_recommendation_algorithm/` | 385 | Hot-zone, single-step, two-step, horizon |
| Extensions | `src/3_extension_task/` | 647 | Temporal, sensitivity, Q-learning |
| Legacy MDP | `src/4_mdp/` | 27 | Redirects to `src/mdp/` |
| Evaluation | `src/eval/` | 1,389 | Static diagnostic, rollout, sanity, offline |
| Forecasting | `src/forecasting/` | 651 | Features, LightGBM/XGBoost, evaluation |
| Graph Learning | `src/graph/` | 239 | OD graph, GraphSAGE, GAT |
| RL | `src/rl/` | 662 | Gym env, DQN, Double-DQN |
| Simulator | `src/simulator/multi_agent/` | 269 | Finite-demand multi-agent engine |
| MDP | `src/mdp/` | 166 | Model-based value iteration |
| Audit | `src/audit/` | 172 | Counterfactual, fairness, stats, temporal |
| Common | `src/common/` | 311 | Config, data loader, logging |

## Potential Problems

### 1. Mixed/Legacy Architecture (HIGH)

**Problem:** The `src/` directory contains BOTH a legacy numbered structure AND a modern clean module structure side-by-side.

| Legacy (numbered) | Modern equivalent | Status |
|---|---|---|
| `src/1_data_clean/` | — | Contains original `clean.py` (169 lines), no modern equivalent |
| `src/2_recommendation_algorithm/` | `src/forecasting/strategy.py` | Strategies re-implemented; `forecasting_strategy.py` is 10-line wrapper, `improved_strategy.py` is 17-line wrapper |
| `src/3_extension_task/` | `src/rl/`, `src/audit/` | Contains `extension_5_qlearning.py` (326 lines) — superseded by `src/rl/dqn.py` |
| `src/4_mdp/` | `src/mdp/` | Nearly empty; `mdp_solver.py` is 3-line redirect |

**Impact:** Developers must understand both structures. Tests and scripts may reference either path. Risk of divergent implementations.

### 2. Orphan `benchmark/` directory (MEDIUM)

Only 2 files: `run_ml_baselines.py` and `ml_benchmark_results.json`. These appear to predate the Phase 13 benchmark platform. The modern benchmark runners live in `scripts/` (e.g., `run_forecasting_benchmark.py`, `run_graph_benchmark.py`, `run_multi_agent_benchmark.py`, `generate_combined_benchmark.py`).

### 3. Orphan `report/` directory (LOW)

Contains `report.tex` (LaTeX template, 87 lines), `qlearning_analysis.md`, and a spurious `__init__.py`. This was likely a student report scaffold. Not referenced by any import or README command.

### 4. Orphan `paper/` directory (LOW)

Single `index.md` (24 lines) — appears to be a landing page draft. Not linked from README.

### 5. `docs/_build/` should be gitignored (MEDIUM)

61 files of Sphinx-built HTML output. These are generated artifacts and should be excluded from Git. Currently only `.doctrees/` is in `.gitignore`.

### 6. Root artifacts not gitignored (LOW)

- `.coverage` — coverage data file at repo root
- `.pytest_cache/` — pytest cache directory
- `.ruff_cache/` — ruff cache directory

### 7. `docs/api/` incomplete (LOW)

Sphinx API docs only cover `src.common` (config, data_loader) and `src.mdp` (model_based, improved_strategy). Modern modules like `forecasting`, `rl`, `simulator`, `graph`, `audit` have no API documentation.

### 8. No `.gitkeep` for empty directories

Several `__init__.py` files are empty (0 lines) and only serve to mark packages: `src/__init__.py`, `src/1_data_clean/__init__.py`, `src/eval/__init__.py`, `tests/__init__.py`, `report/__init__.py`.

### 9. `outputs/` bloat (LOW)

43 files in `outputs/`, including 37 top-level reports and 6 smoke test results. Many are intermediate results. Consider whether all need to be checked in.

### 10. Missing `app/` and `web/` directories

The Phase 15 target structure mentions `app/` and `web/` but these do not exist in the current repository.

## Summary

| Metric | Count |
|---|---|
| Total tracked files | ~165 (excluding caches) |
| Python source files | 82 |
| Total Python lines | ~7,000 |
| Identified problems | 10 |
| HIGH severity | 1 |
| MEDIUM severity | 2 |
| LOW severity | 7 |

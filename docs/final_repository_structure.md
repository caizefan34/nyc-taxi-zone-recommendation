# Final Repository Structure

> Phase 15 cleanup result | 2026-07-26

## Current structure (post-cleanup)

```text
.
├── .github/workflows/            CI (Python lint/test, LaTeX build, Pages deploy)
├── archive/                       Deprecated code preserved for history
│   ├── benchmark/                 Old ML baselines (superseded by scripts/)
│   ├── paper/                     Incomplete landing page draft
│   ├── report/                    Orphan LaTeX student report
│   └── src/4_mdp/                Legacy MDP redirect (→ src/mdp/)
├── assets/                        Static images (social preview, comparison charts)
├── configs/
│   ├── config.yaml                Unified project configuration
│   └── README.md                  Config documentation
├── data/
│   ├── meta/                      Taxi zone lookup (CSV + zip)
│   ├── processed/                 Trained models, cleaned datasets, predictions
│   └── raw/                       Original 2023-01 yellow trip data
├── docs/
│   ├── api/                       Sphinx RST API docs (config, data_loader, mdp)
│   ├── _build/                    Sphinx HTML output (should be gitignored)
│   ├── *.md                       Research documentation (forecasting, graph, RL, etc.)
│   └── *_audit*.md                Phase 15 audit deliverables
├── examples/                      basic_usage.py demo
├── notebooks/                     demo_synthetic_data.ipynb
├── outputs/                       Checked-in benchmark reports and audit evidence
│   └── tmp/                       Smoke test outputs
├── scripts/
│   ├── README.md                  Script classification guide
│   ├── *.py                       15 active experiment/benchmark runners
│   └── archive/                   Empty (no deprecated scripts)
├── src/
│   ├── 1_data_clean/              Data pipeline (Phase 1)
│   ├── 2_recommendation_algorithm/ Strategy implementations (Phase 1)
│   ├── 3_extension_task/          Extensions: temporal, sensitivity, Q-learning (Phase 1)
│   ├── audit/                     Statistical audit tools (Phase 6-8)
│   ├── common/                    Config, data loader, logging
│   ├── eval/                      Evaluation cores: NDCG, rollout, sanity
│   ├── forecasting/               Demand/fare forecasting (Phase 2)
│   ├── graph/                     OD graph + GNN features (Phase 3)
│   ├── mdp/                       Model-based MDP solver
│   ├── rl/                        DQN/Double-DQN baselines (Phase 4)
│   └── simulator/multi_agent/     Finite-demand competition simulator (Phase 3)
├── tests/                         24 test files, ~54 test functions, 100% module coverage
├── pyproject.toml                 Project metadata and dependencies
├── README.md                      Main documentation
├── Makefile                       Convenience targets
├── Dockerfile + docker-compose.yml Container support
├── requirements.txt               Pinned dependencies
├── CHANGELOG.md                   Release history
├── LICENSE                        MIT
├── CONTRIBUTING.md                Contribution guide
├── CODE_OF_CONDUCT.md             Code of conduct
└── SECURITY.md                    Security policy
```

## Directory responsibilities

| Directory | Responsibility |
|---|---|
| `src/` | Core library: data pipeline, strategies, forecasting, RL, simulation, evaluation |
| `scripts/` | Reproducible experiment runners and benchmark generators |
| `tests/` | Unit and integration tests (100% module coverage) |
| `configs/` | Single YAML config with all hyperparameters |
| `docs/` | Research documentation, API docs, audit deliverables |
| `outputs/` | Checked-in reproducible benchmark results |
| `data/` | Raw, processed, and meta data (large files gitignored) |
| `assets/` | Static images for README and documentation |
| `archive/` | Deprecated code preserved with migration notes |
| `.github/` | CI workflows |

## Directories NOT present

| Directory | Reason |
|---|---|
| `app/` | Not part of current codebase (no web/API server) |
| `web/` | Not part of current codebase (no frontend) |
| `benchmark/` | Archived → `archive/benchmark/` |

## Architecture notes

1. **Legacy numbered directories** (`src/1_*`, `src/2_*`, `src/3_*`) coexist with clean module names. They contain the canonical implementations. A future refactor (Phase 16+) could migrate them into the target structure shown in Task 4, but this requires updating all test and script imports.

2. **Single config source:** One `config.yaml` for the entire project.

3. **No dead code:** All modules are imported and tested. No orphan files remain in active directories.

4. **Git history preserved:** All moves used `git mv` (for `src/4_mdp/`, `report/`, `paper/`, `benchmark/`).

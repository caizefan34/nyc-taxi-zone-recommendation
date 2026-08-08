# Changelog

All notable changes to this project are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.0] — Platform Completion (2026-08-08)

### Added
- Benchmark CLI (`benchmark/run.py`) with `--model`, `--city`, `--seed`, `--leaderboard`
- Result-schema validator (`benchmark/schemas/validator.py`)
- Public leaderboard generator (`docs/leaderboard.md`)
- `/simulate` and `/evaluate` REST endpoints (multi-agent rollout + offline metrics)
- LLM mobility agent scaffold (`src/agents/`) — tool-using, echo-mode, no provider required
- Provider-backed planners (`src/agents/planners.py`): `AnthropicPlanner` (`claude-sonnet-5`), `OpenAICompatiblePlanner` (any OpenAI-compatible endpoint via stdlib `urllib`), and `planner_from_env()` — flip echo → real provider by setting `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`, no code change
- `.[agent]` optional extra (`anthropic` SDK, lazily imported)
- Repository audit (`docs/repository_audit.md`)
- Research note: multi-agent policy-adoption saturation (`docs/research/multi_agent_market_effect.md`)
- `POST /simulate` / `POST /evaluate` documented in `docs/index.rst` platform toctree

### Changed
- README results restored to match checked-in benchmark artifacts (GraphSAGE MAE, multi-agent +$531.16)
- Docker api image now bakes in `data/processed/` + `outputs/` so all endpoints work out of the box
- `.dockerignore` updated to include processed data and outputs in the api build context
- `docker_setup.md` rewritten to match current services and data handling
- Fixed pyproject.toml: `dependencies` moved under `[project]` (was parsed as `project.urls.dependencies`, breaking `pip install` and Docker builds)
- ROADMAP: LLM mobility agent scaffold marked complete

### Fixed
- `test_report_consistency` failures — README headline metrics now match checked-in artifacts
- LLM agent test capitalization + deprecated `datetime.utcnow()`

### Verified
- 448 tests pass (436 + 12 new provider-planner tests)
- `ruff check src/ tests/ benchmark/ scripts/` clean
- Docker api + demo images build and serve all endpoints; compose config valid
- Sphinx docs build with `-W` (warnings-as-errors) now passes: **0 warnings** (was 95 — 83 unreferenced-doc `toc.not_included` + 12 xref/highlighting/image). Orphaned archive docs are suppressed via `suppress_warnings = ["toc.not_included"]` in `docs/conf.py` and remain reachable by URL; real defects still fail the build.
- CI now enforces the docs `-W` build (new `docs` job in `ci.yml`)

### Fixed
- CI clean-clone break: `tests/test_api_simulate_evaluate.py` `/simulate` tests required gitignored `data/processed/validation_uncleaned.parquet` and would fail in CI. They now `skipif` when the data is missing (matching `test_baseline_1.py`); `/evaluate` tests use tracked `outputs/*.json` and always run.

---

## [3.0.0] — Decision Intelligence Platform (2026-08-08)

### Added
- Unified decision engine with rich metadata recommendation schema
- REST API (FastAPI): `/health`, `/ready`, `/v1/recommendations`, `/v1/demand/forecast`
- Docker Compose one-click deployment (API + Demo) with health checks
- Multi-stage Dockerfile (api, demo, test targets)
- Model registry with file-based versioning
- Structured observability (logging, request latency, metrics snapshot)
- Shadow evaluation mode (record decisions, don't execute)
- A/B testing framework with bootstrap CIs and effect sizes
- Constraint-aware policy layer
- Trajectory-aware offline policy evaluation (WIS, sequential DR)
- Implicit Q-Learning (IQL) offline RL baseline
- Reproducible OPE benchmark with fixed-seed trajectory bootstrap
- Per-driver trajectory collection with behavior propensities and terminal markers
- CI matrix (Python 3.10/3.12 + Docker build smoke), 402 tests
- Enterprise config profiles (default, api, research, production)
- Cross-city abstraction layer (CityAdapter interface, NYC reference)

### Changed
- README redesigned with collaboration guide, star history, and DOI badges
- Landing page (`pages/index.html`) fully revamped with modern dark theme
- Social preview SVG redesigned
- Academic paper draft expanded to full manuscript with methodology, results, references

### Fixed
- OPE trajectory bootstrap implementation
- Leakage-safe evaluation protocol enforcement

---

## [2.0.0] — Research Benchmark (2026-07-26)

### Added
- Multi-year NYC TLC data pipeline (2022–2025) with Polars processing and strict temporal splits
- Leakage-safe demand forecasting: LightGBM, XGBoost, Ensemble (MAE 1.49)
- OD graph features: GraphSAGE, GAT, OD Messages
- Dynamic multi-agent finite-demand simulator (v2) with calibration layer
- Calibration framework: fare RMSE, travel MAE, demand KL divergence
- DQN and Double DQN baselines on Gymnasium environment
- IQL (Implicit Q-Learning) offline RL with double-clipped ensemble critics
- Three OPE methods: FQE, WIS, Doubly Robust with bootstrap CIs (2000 resamples)
- Statistical benchmark: paired bootstrap comparisons, Cohen's d effect sizes
- Cross-year robustness evaluation (2022–2025) with drift detection
- Experiment manifest for full pipeline reproduction
- Paper figures (architecture, forecast, policy, calibration, benchmark)
- Research paper draft in academic format
- Reproduction guide with step-by-step commands
- 274 unit tests

### Changed
- README restructured with architecture overview, results tables, limitations
- Simulator architecture extended with calibration module
- Benchmark framework enhanced with OPE and statistical rigor

### Fixed
- OPE Doubly Robust implementation with proper bootstrap CIs
- Lint compliance across all source files (ruff check passes)

### Known Limitations
- Offline RL trajectories are simulator-generated, not real logged data
- IQL and DQN use different reward scales — not directly comparable
- All RL policies use single training seed
- OPE not validated against ground-truth online deployment
- Zone demand KL divergence unchanged after calibration
- Cross-year drift detected in 2024 (MAE 3.24)

---

## [1.0.0] — Research Foundation (2026-07-25)

### Added
- Two-step finite-horizon planning algorithm: pickup probability, expected fare, transfer value
- Three strategies: Hot Zone (Baseline), Single-Step Utility, Two-Step Planning
- MDP Value Iteration solver
- Data cleaning pipeline for NYC TLC Yellow Taxi data
- Dijkstra shortest-path travel time matrix
- OD transition probability matrix estimation
- Evaluation framework: NDCG@3, Hit@3, utility metrics, simulation rollouts
- Q-learning baseline comparison
- Interactive analysis and recommendation CLI
- Temporal demand pattern analysis
- Parameter sensitivity grid search
- Ablation study quantifying each component contribution
- Unified YAML configuration system with dot-notation access
- Centralized data loading
- Structured logging
- 41 unit tests
- CI/CD pipeline (ruff lint → pytest → coverage)
- Docker support
- LaTeX report with full results
- MIT License

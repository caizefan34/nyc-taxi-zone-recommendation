# Changelog

## v2.0 Research Release (2026-07-26)

### Added
- Dynamic supply-demand simulator (v2) with configurable demand-supply ratios
- Offline RL pipeline (IQL) with synthetic buffer training
- OPE evaluation (FQE, Doubly Robust)
- Calibration validation (3 dimensions: fare, travel time, demand)
- Cross-year robustness benchmark (2022-2025)
- Latency and memory benchmarks for all policies
- Benchmark automation and paper figures generation
- Research paper draft and reproduction guide

### Fixed
- OPE confidence interval implementation
- Pipeline CI reliability
- Leakage-safe evaluation protocol

### Known Limitations
- Offline RL trajectories are simulator-generated, not real logged data
- Temporal drift detected in 2024 (MAE 3.24 vs baseline 1.49)
- Graph signals do not improve forecasting (CIs cross zero)
- Better forecasting does not guarantee better policy

---
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-26

### Added
- Multi-year data pipeline (2022--2025) with Polars-based processing
- Dynamic supply-demand simulator v2 with calibration layer
- Calibration framework (demand, fare, travel time, reward) with config
- Implicit Q-Learning (IQL) offline RL implementation
- Offline RL data protocol with standardized trajectory format (state, action, reward, next_state, done, behavior_prob)
- Off-policy evaluation: Fitted Q Evaluation (FQE), Doubly Robust (DR), Weighted Importance Sampling (WIS)
- Bootstrap confidence interval computation (95%, 2000 resamples) for all comparisons
- Cross-year robustness benchmark (2022--2025) with drift detection
- Calibration validation report with fare RMSE and travel MAE metrics
- Simulator validation against real NYC TLC statistics
- Benchmark statistics with Cohen'''s d effect sizes and paired comparisons
- Paired bootstrap comparison across all model pairs
- Experiment manifest for full pipeline reproduction
- Unified YAML configs (dataset, model, simulator, RL, calibration)
- Research release report with problem definition, method, results, limitations

### Changed
- README restructured to: Overview, System Architecture, Key Contributions, Experimental Results, Honest Limitations, Quick Start
- Simulator architecture extended with calibration module
- Benchmark framework enhanced with OPE and bootstrap statistics
- Documentation reorganized with reproduction guide, release checklist, and research report

### Fixed
- Lint compliance across all source files (ruff check passes with zero errors)
- Ambiguous variable names in figure generation scripts
- Import sorting in evaluation scripts
- Unused import removal

### Known Limitations
- Offline RL (IQL) trajectories are simulator-generated, not real driver data
- IQL and DQN operate on different reward scales -- not directly comparable
- All RL policies use single training seed
- OPE not validated against ground-truth online deployment
- Zone demand KL divergence unchanged after calibration
- Cross-year drift detected in 2024 (MAE 3.24)
- Single-month evaluation window (January 2023)

## [1.0.0] - 2026-07-25

### Added
- Two-step finite-horizon planning algorithm with pickup probability, expected fare,
  and future transfer value modeling
- Three recommendation strategies: Hot Zone (Baseline 1), Single-Step Utility
  (Baseline 2), and Two-Step Planning (Ours)
- MDP Value Iteration solver as an alternative approach
- Data cleaning pipeline for NYC TLC Yellow Taxi trip data
- Dijkstra shortest-path travel time matrix computation
- OD transition probability matrix estimation from training data
- Comprehensive evaluation framework with static metrics (NDCG@3, Hit@3)
  and simulation rollout (avg daily fare, pickups, idle time)
- Q-learning baseline comparison
- Interactive analysis and recommendation CLI tool
- Temporal analysis of demand patterns
- Parameter sensitivity grid search
- Ablation study quantifying each component contribution
- Unified configuration system (YAML + dot-notation access)
- Centralized data loading to eliminate code duplication
- Structured logging replacing print statements
- 41 unit tests (26 pass without data, 15 skip gracefully)
- CI/CD pipeline (ruff lint → pytest test → coverage upload)
- Docker support for reproducible builds
- LaTeX report with full experimental results
- Comprehensive documentation (problem statement, methodology, ablation study)
- MIT License
## [2.0.0] - 2026-07-26

### Added
- Multi-year NYC TLC data pipeline (2022-2025) with strict temporal split
- LightGBM forecasting with feature engineering (lags, rolling stats, neighbor features)
- Forecasting ensemble blending (0.75 LightGBM + 0.25 historical)
- DynamicSimulator v2: event-driven multi-agent simulation with supply-dependent pickup probability
- Simulator calibration layer (demand, fare, travel time, reward dimensions)
- Simulator reality validation against real TLC distributions (KL divergence, Wasserstein distance)
- IQL (Implicit Q-Learning) offline RL with double-clipped ensemble critics
- Three OPE methods: FQE, Weighted Importance Sampling, Doubly Robust with bootstrap CIs
- Statistical benchmark with paired bootstrap comparisons and Cohen's d effect sizes
- Cross-year robustness evaluation (2022-2025) with drift detection
- Calibration validation framework (fare RMSE improvement 8.88 -> 3.11)
- Policy evaluation report with confidence intervals and policy ranking
- Paper figures (architecture, forecast comparison, policy comparison, calibration, benchmark)
- Research paper draft in academic format
- Reproduction guide with step-by-step commands
- Experiment manifest recording all configuration parameters
- Release checklist for publication readiness
- 274 unit tests (15 skip gracefully for data-dependent tests)

### Changed
- Restructured README with architecture overview, results tables, and honest limitations
- Upgraded from single-year to multi-year data processing pipeline
- Enhanced offline buffer with trajectory_id, timestamp, behavior_policy_probability fields
- Expanded documentation suite with audit reports and research release report

### Fixed
- Calibration not being a simple reward scale: now supports 4 independent dimensions
- OPE Doubly Robust implementation with proper bootstrap confidence intervals
- Lint compliance across all source and test files

### Known Limitations
- All RL trajectories are simulator-generated, not real driver behavior
- Policy comparisons use single training seed
- Temporal drift detected in 2024 data (MAE 3.24)
- IQL and DQN use different reward scales, direct revenue comparisons unreliable
- No online deployment validation available

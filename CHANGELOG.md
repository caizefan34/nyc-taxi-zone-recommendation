# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

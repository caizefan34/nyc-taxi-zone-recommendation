# Architecture Audit Report

**Generated:** 2026-08-07
**Repository:** urban-mobility-ai
**Branch:** master (a26603f)

---

## Executive Summary

The repository is a mature, research-grade benchmark platform for NYC taxi zone recommendation with 322 passing tests, strong CI, and rigorous scientific methodology. It has significant infrastructure already but is organized as a "research code collection" rather than a "platform." The core opportunity is to bridge research and engineering without compromising either.

---

## A. Current Architecture

### Top-Level Structure

```
├── src/                    # Core source (mixed research + shared)
│   ├── 1_data_clean/       # Data pipeline (raw split, cleaning, stats)
│   ├── 2_recommendation_algorithm/  # Policies: Hot Zone, Single-Step, Two-Step
│   ├── 3_extension_task/   # Temporal analysis, Q-learning, sensitivity
│   ├── common/             # Config, DataLoader, logging, MLflow
│   ├── data/               # Multi-year data pipeline, download
│   ├── eval/               # Static diagnostics, rollout, sanity check
│   ├── evaluation/         # Historical replay (lightweight)
│   ├── features/           # External features (airport, weather, calendar, events)
│   ├── forecasting/        # LightGBM, XGBoost, features, recursive forecast
│   ├── graph/              # OD graph builder, GraphSAGE/GAT models
│   ├── interfaces/         # ABCs (ForecastModel, Policy, RLPolicy) + registry + adapters
│   ├── mdp/                # Model-based value iteration
│   ├── rl/                 # Gymnasium env, DQN/DoubleDQN, offline RL (IQL), mean-field
│   └── simulator/          # Multi-agent v1 + v2, calibration, validation
├── scripts/                # 30+ experiment runners and utility scripts
├── tests/                  # 44 test files, 322 tests passing
├── configs/                # YAML configs: config.yaml, model.yaml, simulator.yaml, etc.
├── docs/                   # 80+ documentation files (many audit reports)
├── outputs/                # Checked-in benchmark results and reports
├── app/                    # Streamlit demo
├── web/                    # GitHub Pages web demo
├── benchmark/              # External benchmark framework (runners, schemas, submissions)
├── examples/               # basic_usage.py, custom_policy_example.py
├── notebooks/              # Jupyter demo notebooks
├── archive/                # Deprecated code with migration notes
├── Dockerfile              # Basic Dockerfile (runs basic_usage.py)
├── Dockerfile.demo         # Demo-specific Dockerfile
├── docker-compose.yml      # Basic compose with nyc-taxi, test, train services
└── Makefile                # 24 targets: train, test, lint, static, rollout, audit, etc.
```

### Dependency Graph

```
data pipeline → zone statistics + travel times → recommendation algorithms
                                                      ↓
forecasting models ← features ← zone statistics → static evaluation
       ↓                                              ↓
  simulator ← travel times ← zone statistics → rollout evaluation
       ↓                                              ↓
  RL environment ← simulator → multi-agent benchmark
       ↓
  offline RL (IQL) / mean-field RL
```

---

## B. Current Research Capabilities

### B1. Forecasting

| Component | Status | Notes |
|---|---|---|
| LightGBM (Poisson demand) | COMPLETE | Production-grade, deterministic |
| XGBoost (Poisson demand) | COMPLETE | Alternative baseline |
| Ensemble (LightGBM + XGBoost) | COMPLETE | Evaluated in benchmark |
| GraphSAGE features | COMPLETE | MAE 1.5037, CI crosses zero |
| GAT features | COMPLETE | Weaker than GraphSAGE |
| Recursive forecasting | COMPLETE | Multi-step without leakage |
| Forecast persistence (joblib) | COMPLETE | ForecastBundle serialization |
| Historical blending | COMPLETE | Blend ML forecast with historical average |

### B2. Policies / Recommendation

| Strategy | Type | Status |
|---|---|---|
| Hot Zone | Heuristic baseline | COMPLETE |
| Single-Step | Greedy utility maximization | COMPLETE |
| Two-Step Horizon | Truncated finite-horizon planning | COMPLETE (primary) |
| MDP Value Iteration | Model-based | COMPLETE |
| DQN | Online RL in simulator | COMPLETE |
| Double DQN | Online RL | COMPLETE |
| IQL | Offline RL | COMPLETE |
| Mean-Field | Multi-agent RL | COMPLETE |
| Forecasting-Enhanced | ML forecast + Single-Step | COMPLETE (negative result) |

### B3. Simulation

| Simulator | Features | Status |
|---|---|---|
| Legacy single-agent | Immutable demand, no competition | COMPLETE |
| Multi-agent v1 | Finite demand, competition, depletion, market saturation | COMPLETE |
| Multi-agent v2 | Dynamic state, supply-demand feedback, richer rewards | COMPLETE |
| Calibration | Simulator calibration framework | COMPLETE |
| Validation | Comparison, temporal, revenue validation | COMPLETE |

### B4. Evaluation

| Method | Status |
|---|---|
| Static diagnostics (NDCG@3, Hit@3, reference utility) | COMPLETE |
| Paired 100-seed rollout | COMPLETE |
| Bootstrap confidence intervals | COMPLETE |
| Statistical tests (paired) | COMPLETE |
| Fairness/exposure analysis | COMPLETE |
| Temporal robustness | COMPLETE |
| Counterfactual estimators (IPS, SNIPS, DR) | COMPLETE |
| Historical replay evaluation | BASIC (simplified) |

---

## C. Current Production Capabilities

| Capability | Status | Notes |
|---|---|---|
| Docker | PARTIAL | Dockerfile exists but only runs basic_usage.py |
| docker-compose | PARTIAL | Basic services: nyc-taxi, test, train |
| API (REST) | MISSING | No FastAPI or Flask API |
| Health checks | MISSING | No /health, /ready endpoints |
| Model registry | PARTIAL | interfaces/registry.py exists but lightweight |
| Model versioning | PARTIAL | ForecastBundle has metadata; no unified system |
| Config management | EXISTS | YAML-based, single config.yaml |
| Logging | EXISTS | Standardized logging utility |
| MLflow tracking | PARTIAL | Wrapper exists; optional dependency |
| CI/CD | STRONG | GitHub Actions: lint, test, coverage |
| Pre-commit hooks | STRONG | ruff, black, mypy, whitespace |
| Benchmark protocol | STRONG | Schema, submission template, external runner |
| Demo | EXISTS | Streamlit + GitHub Pages web demo |
| Monitoring | MISSING | No Prometheus/metrics abstraction |
| Authentication | MISSING | No auth abstraction |

---

## D. Missing Components (Gap Analysis)

### D1. High Priority

1. **Unified Decision Engine** - No `Recommendation` dataclass with rich metadata; policies return bare zone_id lists
2. **Production Inference API** - No REST API for serving recommendations
3. **Shadow Evaluation** - No framework for comparing AI recommendations against actual outcomes without execution
4. **A/B Testing Framework** - No statistical A/B test infrastructure
5. **Fleet Operations Dashboard** - Current demo is consumer-facing; no operations/fleet intelligence mode
6. **Cross-City Architecture** - NYC hardcoded throughout; cross_city_extension.md is a design doc only

### D2. Medium Priority

7. **Constraint Layer** - No constraint-aware policy wrapper (max distance, zone concentration limits)
8. **Observability** - No structured request logging with latency tracking
9. **Enterprise Config System** - Single config.yaml; no profile hierarchy (research/api/production)
10. **Decision-Aware Research Framework** - No experiments testing correlation between forecast accuracy and decision quality
11. **Market Dynamics Studies** - Multi-agent simulator exists but no systematic adoption-rate sweep

### D3. Lower Priority (Nice to Have)

12. **Enterprise Documentation** - No pilot.md, deployment.md, security.md for enterprise users
13. **Developer Examples** - Only basic_usage.py; no API client example, forecast example
14. **Reproducibility Infrastructure** - No experiment tracking (git commit, seed, dataset version per run)

---

## E. Technical Debt Assessment

| Issue | Severity | Location |
|---|---|---|
| Numbered directory names (1_data_clean, 2_recommendation_algorithm) | LOW | src/ |
| archive/ contains ~15 files with stale code and migration notes | LOW | archive/ |
| docs/ has 80+ files, many are historical audits | LOW | docs/ |
| Duplicate simulator implementations (v1, v2) | MEDIUM | src/simulator/ |
| Mixed eval/ and evaluation/ directories | LOW | src/ |
| Historical replay is simplified (placeholder) | MEDIUM | src/evaluation/ |
| interfaces/registry.py has hardcoded models | LOW | src/interfaces/ |
| No .env.example or secrets management | MEDIUM | root |

---

## F. Research Risks

1. **Forecast-decision gap**: Better forecasting does not automatically improve decisions (already demonstrated: forecast-enhanced Single-Step scores -$17.88/day). This is a feature (honest science), but the platform needs formal experiments around this.

2. **Policy adoption saturation**: Two-Step has 70.33% airport exposure, Gini 0.982. If many drivers adopt the same policy, saturation risk is high. Already noted but not systematically studied.

3. **Simulator-data gap**: Multi-agent simulator still omits congestion, airport queues, endogenous demand, strategic adaptation. Well-documented but limits real-world applicability.

4. **Graph features insignificance**: GraphSAGE and GAT show no statistically significant improvement over non-graph LightGBM. This is correctly reported but represents dead-end research direction unless new approaches found.

---

## G. Commercialization Risks

1. **No production API**: Cannot be integrated without building one
2. **No Docker deployment**: docker-compose only runs make help; no service-oriented deployment
3. **No fleet integration layer**: Policies operate on individual state, not fleet-level optimization
4. **No shadow/A-B mode**: Cannot validate recommendations against real outcomes
5. **No enterprise documentation**: No onboarding path for potential pilot partners

---

## H. Strengths to Preserve

1. **Scientific rigor**: Clear distinction between static metrics, simulator outcomes, and production revenue
2. **Reproducibility**: Fixed random seeds, deterministic training, checked-in reference metrics
3. **Comprehensive testing**: 322 tests, 15 skipped (external deps), strong coverage
4. **Honest reporting**: Negative results reported (forecast doesn't help, graph features don't help)
5. **Leakage safety**: Temporal splits are strictly prior-only
6. **Simulator boundary documentation**: Clear caveats about what the simulator does and doesn't model

---

## I. Recommended Refactoring Approach

### Principle: Reuse > Refactor > Rewrite

1. **Keep all existing src/ code** - Add new modules alongside, don't move unless necessary
2. **Add api/ at top level** - New FastAPI application, not touching existing code
3. **Add src/decision/** - New Decision Engine module that wraps existing policies
4. **Add src/evaluation/shadow/** - New shadow evaluation module
5. **Add src/evaluation/ab/** - New A/B testing module
6. **Add src/cities/** - City abstraction layer with NYC adapter
7. **Add configs/ profiles** - New config files alongside existing config.yaml
8. **Enhance existing** app/app.py, Dockerfile, docker-compose.yml - Don't replace

### Migration Strategy

- All old interfaces maintained via adapters in src/interfaces/
- New Decision Engine wraps existing strategy functions
- API calls existing code through Decision Engine
- No breaking changes to existing research code

---

## J. Quick Wins (Low Effort, High Impact)

1. Add `Recommendation` dataclass with rich metadata
2. Create FastAPI with /health, /ready endpoints
3. Polish Docker setup for `docker compose up`
4. Add .env.example
5. Restructure README with platform narrative
6. Create docs/enterprise/ directory with pilot documentation
7. Add examples/api_client.py

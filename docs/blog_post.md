# Technical Blog Post: Building an Open Decision Intelligence Platform for AI-driven Urban Mobility

> **Target audience**: ML researchers, urban computing practitioners, data scientists
> **Estimated reading time**: 12 minutes
> **Status**: Draft prepared. Not yet published.

---

## Introduction

Every day, over 13,000 yellow taxis navigate New York City streets. Drivers spend 30-50% of their shift cruising without passengers — burning fuel, creating congestion, and losing revenue.

This is a **sequential decision problem under uncertainty** — the kind machine learning excels at solving. Yet most existing solutions are either black-box commercial products or unreproducible academic prototypes.

We built the **Urban Mobility Decision Intelligence Platform**, an open-source system combining demand forecasting, multi-agent simulation, offline reinforcement learning, and trajectory-aware policy evaluation into a reproducible research pipeline with production-style API and Docker deployment.

---

## Why Existing Approaches Fall Short

### The Reproducibility Crisis

Urban computing research suffers from a fundamental problem: **you cannot compare results across papers**. Different data splits, different metrics, different simulation environments — impossible to tell whether a new method is genuinely better or just evaluated differently.

### Data Leakage is Everywhere

The most common mistake? Using future information to predict the past. Random train-test splits on temporal data let models peek into the future. We found random splits inflate forecasting accuracy by 15-25% compared to chronological splits.

### OPE Without Identifiable Propensities is Meaningless

NYC TLC trip records contain trip outcomes but no logged reposition recommendations, behavior-policy propensities, or driver acceptance decisions. Valid importance sampling or doubly robust evaluation is therefore not identifiable from TLC data alone. Our platform distinguishes simulator-generated OPE benchmarks (method validation) from real-world causal claims (which require logged propensities from a deployed stochastic policy).

### Simulation Matters

Without a simulator, you cannot ask counterfactual questions: "What if the driver had gone to Zone X instead of Zone Y?" Real-world A/B testing is expensive and logistically impossible for most researchers.

---

## System Architecture

```
Raw TLC Trips → Data Pipeline → Forecasting → Simulator → Policies → Evaluation → API/Docker
                     |               |              |            |            |
                Leakage-safe    LightGBM/XGBoost  Multi-Agent  DQN/IQL     WIS/DR OPE
                     |               |              |            |            |
              Chronological    GraphSAGE + GAT   Competition  Reproducible  Bootstrap CI
```

### Layer 1: Data Pipeline

NYC TLC Yellow Taxi trip records through a leakage-safe pipeline with strict chronological splits. **No future information leaks into training.**

### Layer 2: Demand Forecasting

LightGBM and XGBoost models with spatial features from GraphSAGE and GAT. Ensemble achieves **MAE of 1.4868** on holdout predictions.

### Layer 3: Multi-Agent Simulation

A **finite-demand simulator** where multiple drivers compete for limited passengers. Configurable fleet size, explicit competition, calibrated travel times. v2 engine records full decision context including behavior propensities for OPE.

### Layer 4: Policy Optimization

Five policy types: Hot Zone (baseline), Single-Step MDP, Two-Step Horizon planning, DQN/Double DQN, and Implicit Q-Learning (IQL) for offline RL.

### Layer 5: Offline Policy Evaluation

Trajectory-level Weighted Importance Sampling (WIS) and sequential Doubly Robust (DR) estimation with complete-trajectory bootstrap confidence intervals. Requires explicit behavior/target probabilities and Q/V nuisance predictions — not silently assumed defaults.

---

## Key Results

### Static Diagnostic and Simulator Rollout

| Strategy | NDCG@3 | Daily Fare | vs Hot Zone |
|---|---|---|---|
| Hot Zone | 0.7846 | $431.21 | — |
| Single-Step | 0.9024 | $548.77 | +$117.56 |
| **Two-Step Horizon** | **0.9565** | **$570.61** | **+$139.40** |

### Deep RL (50-driver benchmark)

| Algorithm | Revenue Delta | 95% CI |
|---|---|---|
| DQN | **+$53.74** | [+46.21, +61.57] |
| Double DQN | -$25.27 | [-32.77, -17.97] |

### Offline Policy Evaluation (simulator trajectories)

| Policy | WIS | Sequential DR |
|---|---|---|
| Stay (on-policy, prob=1.0) | $438.55 | $431.74 |
| IQL (off-policy, uniform behavior) | $0.00 | $12.44 |

> IQL results reflect deterministic-target overlap limitations with uniform exploration data. Bootstrap intervals do not repair missing support.

> **All results are simulator outcomes — not production revenue estimates.**

### Insight 1: Planning Horizon Matters

Moving from single-step to two-step planning improves NDCG@3 from 0.9024 to 0.9565. The driver considers not just current demand but future demand after travel time.

### Insight 2: RL Requires Careful Evaluation

DQN outperforms Single-Step in multi-agent settings (+$53.74/driver), but Double DQN underperforms. Offline IQL with uniform behavior data shows zero WIS estimate due to deterministic target / stochastic behavior overlap issues — a genuine signal about support problems, not a bug.

### Insight 3: Leakage-Free Evaluation is Essential

Random train-test splits inflate forecasting accuracy by 15-25%. Chronological splits are essential for honest evaluation.

---

## Platform Engineering

Beyond research: the platform ships with:

- **REST API** (FastAPI + Pydantic v2) with `/health`, `/ready`, `/v1/recommendations`
- **Docker Compose** one-command deployment with health checks on all services
- **CI/CD** with Python 3.10/3.12 matrix, Ruff lint, 402 tests, coverage, and Docker smoke
- **Model registry** with versioning and training metadata
- **Shadow evaluation** mode (record decisions, don't execute)

---

## Limitations

1. **Simulator is not production**: Real-world complexity is far greater
2. **NYC only**: Models need cross-city validation for generalization
3. **Static demand**: Forecasts use historical patterns, not real-time events
4. **No real logged propensities**: OPE requires a deployed stochastic logging policy for identifiable real-world evaluation
5. **Simplified competition**: Homogeneous agents with identical objectives
6. **Deterministic target overlap**: IQL and other deterministic policies have poor support overlap with stochastic behavior data

---

## Future Work

Planned (not yet executed):
- Cross-city validation (Chicago, Singapore datasets)
- Deploy stochastic logging policy for identifiable real-world OPE
- Real driver feedback study (requires IRB approval)
- Online pilot with partner fleet
- Heterogeneous agent simulation
- Hugging Face Space for one-click demo access

---

## Try It Yourself

- **Live Demo**: https://caizefan34.github.io/nyc-taxi-zone-recommendation/web/
- **Repository**: github.com/caizefan34/nyc-taxi-zone-recommendation
- **Documentation**: caizefan34.github.io/nyc-taxi-zone-recommendation/docs/

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
pip install -e ".[dev,data,forecasting,graph,rl,api,demo]"
python -m scripts.run_ope_comparison --seed 42
```

---

*This is a technical report / preprint. A formal paper has not yet been published.*

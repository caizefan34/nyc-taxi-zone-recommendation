# Technical Blog Post: Building an Open Benchmark Platform for AI-driven Urban Mobility Decision Making

> **Target audience**: ML researchers, urban computing practitioners, data scientists
> **Estimated reading time**: 12 minutes
> **Status**: Draft prepared. Not yet published.

---

## Introduction

Every day, over 13,000 yellow taxis navigate New York City streets. Drivers spend 30-50% of their shift cruising without passengers — burning fuel, creating congestion, and losing revenue.

This is a **sequential decision problem under uncertainty** — the kind machine learning excels at solving. Yet most existing solutions are either black-box commercial products or unreproducible academic prototypes.

We built the **Dynamic Urban Mobility Decision System**, an open-source benchmark platform combining demand forecasting, multi-agent simulation, and offline reinforcement learning into a reproducible research pipeline.

---

## Why Existing Approaches Fall Short

### The Reproducibility Crisis

Urban computing research suffers from a fundamental problem: **you cannot compare results across papers**. Different data splits, different metrics, different simulation environments — impossible to tell whether a new method is genuinely better or just evaluated differently.

### Data Leakage is Everywhere

The most common mistake? Using future information to predict the past. Random train-test splits on temporal data let models peek into the future. We found random splits inflate forecasting accuracy by 15-25% compared to chronological splits.

### Simulation Matters

Without a simulator, you cannot ask counterfactual questions: "What if the driver had gone to Zone X instead of Zone Y?" Real-world A/B testing is expensive and logistically impossible for most researchers.

---

## System Architecture

```
Raw TLC Trips -> Data Pipeline -> Forecasting -> Simulator -> Policies -> Benchmark
                      |               |              |            |
                 Leakage-safe    LightGBM/XGBoost  Multi-Agent  DQN/MDP
                      |               |              |            |
               Chronological    GraphSAGE + GAT   Competition  Reproducible
```

### Layer 1: Data Pipeline

NYC TLC Yellow Taxi trip records (2009-2023) through a leakage-safe pipeline with strict chronological splits. **No future information leaks into training.**

### Layer 2: Demand Forecasting

LightGBM and XGBoost models with spatial features from GraphSAGE and GAT. Ensemble achieves **MAE of 1.4868** on holdout predictions.

### Layer 3: Multi-Agent Simulation

A **finite-demand simulator** where multiple drivers compete for limited passengers. Demand depletes as drivers pick up passengers, with realistic travel times and shift constraints.

### Layer 4: Policy Optimization

Four policy types: Hot Zone (baseline), Single-Step MDP, Two-Step Horizon planning, and DQN/Double DQN with masked action spaces.

---

## Key Results

| Strategy | NDCG@3 | Daily Fare | vs Baseline |
|---|---|---|---|
| Hot Zone | 0.7846 | $431.21 | — |
| Single-Step | 0.9024 | $548.77 | +$117.56 |
| **Two-Step Horizon** | **0.9565** | **$570.61** | **+$139.40** |
| DQN | — | $466.59 | +$53.74 |

> **Warning**: All results are simulator outcomes — not production revenue estimates.

### Insight 1: Planning Horizon Matters

Moving from single-step to two-step planning improves NDCG@3 from 0.9024 to 0.9565. The driver considers not just current demand but future demand after travel time.

### Insight 2: RL is Harder Than It Looks

DQN underperforms the two-step MDP planner due to sample inefficiency and credit assignment in multi-agent settings.

### Insight 3: Leakage-Free Evaluation is Essential

Random train-test splits inflate forecasting accuracy by 15-25%. Chronological splits are essential for honest evaluation.

---

## Limitations

1. **Simulator is not production**: Real-world complexity is far greater
2. **NYC only**: Models need cross-city validation for generalization
3. **Static demand**: Forecasts use historical patterns, not real-time events
4. **No real deployment**: All evaluations are offline only
5. **Simplified competition**: Homogeneous agents with identical objectives

---

## Future Work

Planned (not yet executed):
- Cross-city validation (Chicago, Singapore datasets)
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
make all
```

---

*This is a technical report / preprint. A formal paper has not yet been published.*

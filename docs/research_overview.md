# Research Overview

> **Dynamic Urban Mobility Decision System** — An open-source benchmark platform for AI-driven urban mobility.

## Problem

Taxi drivers spend 30–50% of their shift cruising for passengers, representing millions in lost revenue and unnecessary congestion annually in NYC alone. Existing approaches to taxi repositioning are often:

- **Rule-based**: cannot adapt to dynamic demand patterns
- **Black-box**: lack interpretability for drivers
- **Unreproducible**: no standardized benchmarks for comparison

## Motivation

We propose a **reproducible, research-grade benchmark platform** that:

1. Combines spatiotemporal demand forecasting with decision optimization
2. Provides a multi-agent simulation environment for fair policy comparison
3. Establishes reproducible evaluation protocols with statistical rigor

## Method

The framework consists of four integrated components:

### 1. Demand Forecasting
- Leakage-safe chronological data splits (strictly prior timestamps)
- LightGBM and XGBoost models with GraphSAGE/GAT spatial embeddings
- Recursive holdout predictions for out-of-sample evaluation

### 2. Multi-Agent Simulation
- Finite-demand economy: drivers compete for a limited pool of passengers
- Configurable fleet size, shift duration, and demand patterns
- Explicit competition mechanics with demand depletion

### 3. Policy Optimization
- Two-step finite-horizon planning (MDP-based)
- DQN and Double DQN with masked action spaces
- Offline RL with IQL for policy learning from historical data

### 4. Benchmark & Audit
- Paired statistical tests (Wilcoxon, bootstrap)
- Horizon sensitivity experiments (1–6 steps)
- Comprehensive audit trails for every metric

## Main Findings

| Strategy | NDCG@3 | Hit@3 | Daily Fare | vs Hot Zone |
|---|---|---|---|---|
| Hot Zone (baseline) | 0.7846 | 0.5842 | \.21 | — |
| Single-Step | 0.9024 | 0.8804 | \.77 | +\.56 |
| Two-Step Horizon | **0.9565** | **0.9714** | **\.61** | **+\.40** |
| DQN (50-driver) | — | — | \.59 | +\.74 vs Single-Step |

**Key insights:**
- Multi-step planning significantly outperforms single-step (NDCG@3: 0.9565 vs 0.9024)
- RL-based policies show promise but are sample-inefficient in this setting
- Demand forecasting MAE of 1.4868 (LightGBM+XGBoost ensemble) enables reliable simulation
- Results are stable across multiple random seeds (validated with multi-seed RL)

## Limitations

> ⚠️ **Important**: All results are **simulator outcomes only**, not production revenue estimates.

1. **Simulator ≠ Production**: The multi-agent simulator abstracts real-world complexity (traffic, driver behavior, passenger preferences)
2. **NYC-specific**: Models trained exclusively on NYC TLC data; generalization to other cities requires cross-city validation
3. **Static demand**: Forecasting uses historical patterns; does not adapt to real-time events
4. **No real-world deployment**: All evaluations are offline; no A/B testing or driver feedback collected
5. **Simplified competition**: Drivers are homogeneous agents; real-world competition is more heterogeneous

## Future Directions

These are **planned activities**, not completed work:

- **Cross-city validation**: Chicago, Singapore taxi datasets (framework designed, not executed)
- **Real driver feedback**: Survey/interview study with NYC taxi drivers (requires IRB approval)
- **Online A/B testing**: Real-time recommendation pilot (requires partnership)
- **Enhanced RL**: Multi-agent RL with heterogeneous driver populations
- **Dynamic rebalancing**: Integration with ride-hailing fleet management

## Reproducibility

All results can be reproduced by running:

```bash
make all
```

This executes the full pipeline: data processing → forecasting → simulation → policy optimization → benchmark evaluation.

See [benchmark_protocol.md](benchmark_protocol.md) for details.

## Citation

If you use this work, please cite:

```bibtex
@software{cai2025urbanmobility,
  author = {Cai, Zefan},
  title = {Urban Mobility Decision Intelligence},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/caizefan34/nyc-taxi-zone-recommendation}
}
```

See [CITATION.cff](../CITATION.cff) for the full metadata.

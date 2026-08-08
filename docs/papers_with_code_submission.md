# Papers With Code — Submission Preparation

> **Status**: Materials prepared for future submission. Not yet submitted.

## Task Description

**Task**: Urban Mobility Decision Optimization (Taxi Repositioning)
**Subtask**: Zone-level recommendation for taxi drivers using historical trip data
**Type**: Sequential decision making under uncertainty

**Problem**: Given historical taxi trip patterns across 263 NYC zones, predict hourly demand and recommend optimal repositioning zones to maximize driver revenue while minimizing cruising time. The decision space is constrained by travel time, shift duration, and competition from other drivers.

## Dataset

**Name**: NYC TLC Yellow Taxi Trip Records
**Source**: [NYC Taxi & Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
**Period**: 2009–2023 (configurable subset)
**Size**: ~1.1 billion trips (full dataset); our pipeline uses ~100M trips

**Preprocessing**:
- Chronological split: training ≤ 2019, validation = 2020, test = 2021+
- Zone aggregation (263 zones from NYC taxi zone shapefile)
- Hourly aggregation with temporal features
- Leakage-safe: all temporal splits are strictly prior (no future information)

**Data splits**:
| Split | Period | Trips |
|---|---|---|
| Training | 2009–2019 | ~80M |
| Validation | 2020 | ~8M |
| Test | 2021–2023 | ~12M |

## Evaluation Metrics

### Primary Metrics
| Metric | Description | Target |
|---|---|---|
| NDCG@3 | Normalized Discounted Cumulative Gain for top-3 zone recommendations | Higher is better |
| Hit@3 | Fraction of queries where true best zone is in top-3 | Higher is better |
| Daily Fare | Simulated daily revenue per driver | Higher is better |

### Secondary Metrics
| Metric | Description |
|---|---|
| Utilization Rate | Fraction of shift spent with passengers |
| MAE | Mean absolute error of demand forecasts |
| Revenue Lift vs Baseline | Improvement over Hot Zone strategy |

## Benchmark Protocol

See [benchmark_protocol.md](benchmark_protocol.md) for the full protocol.

**Key aspects**:
- **Reproducible**: All metrics checked into repository; make all recreates results
- **Leakage-safe**: Strict chronological splits prevent future information leakage
- **Statistical rigor**: Paired Wilcoxon tests and bootstrap confidence intervals
- **Multi-seed**: RL policies evaluated across 3+ random seeds

## Baseline Models

| Model | Type | Key Features |
|---|---|---|
| Hot Zone | Rule-based | Always moves to historically busiest zone |
| Single-Step | MDP Planning | One-step lookahead demand optimization |
| Two-Step Horizon | MDP Planning | Two-step finite-horizon with travel constraints |
| DQN | RL | Deep Q-Network with masked action space |
| Double DQN | RL | Double DQN for reduced overestimation bias |
| IQL | Offline RL | Implicit Q-Learning from historical transitions |
| LightGBM+XGBoost | Forecasting | Ensemble demand prediction |

## Results Table

| Model | NDCG@3 | Hit@3 | Daily Fare (\$) | vs Hot Zone |
|---|---|---|---|---|
| Hot Zone | 0.7846 | 0.5842 | 431.21 | — |
| Single-Step | 0.9024 | 0.8804 | 548.77 | +117.56 |
| Two-Step Horizon | **0.9565** | **0.9714** | **570.61** | **+139.40** |
| DQN (50-driver) | — | — | 466.59 | +53.74* |
| LightGBM+XGBoost | MAE 1.4868 | — | — | — |

\* vs Single-Step policy in multi-agent setting

> ⚠️ All results are simulator outcomes. See [limitations](#limitations).

## Limitations

1. Simulator outcomes only — not production revenue estimates
2. NYC-specific training data — cross-city generalization not yet validated
3. Simplified driver behavior model — homogeneous agents, no learning from experience
4. Static demand forecasts — no real-time adaptation to events

## License

MIT License. See [LICENSE](../LICENSE).

## Citation

`ibtex
@software{cai2025urbanmobility,
  author = {Cai, Zefan},
  title = {Dynamic Urban Mobility Decision System: An Open-Source Benchmark Platform},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/caizefan34/urban-mobility-ai}
}
`

See [CITATION.cff](../CITATION.cff) for full metadata.

## Repository

**URL**: https://github.com/caizefan34/urban-mobility-ai
**Live Demo**: https://caizefan34.github.io/urban-mobility-ai/web/
**Documentation**: https://caizefan34.github.io/urban-mobility-ai/docs/

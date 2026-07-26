# Benchmark Protocol v2.0

## Dataset

- **Source:** NYC TLC Yellow Taxi Trip Records (2022-2025)
- **Zones:** 263 official NYC taxi zones
- **Splits:** Strict chronological (train: 2022-2023, val: 2024, test: 2025)
- **Format:** Parquet files with cleaned trip records

## Task Definition

Given a taxi driver'"'"'s current zone and time of day, recommend the top-3 zones to maximize expected revenue.

### Forecasting Sub-task

Predict zone-level pickup demand 30 minutes ahead.

### Decision Making Sub-task

Generate ranked zone recommendations.

### Offline RL Sub-task

Learn a policy from fixed trajectories to maximize cumulative reward.

## Metrics

### Forecasting

| Metric | Definition | Higher is Better |
|--------|------------|:----------------:|
| MAE | Mean Absolute Error of predicted vs actual pickups | No |
| RMSE | Root Mean Squared Error | No |
| SMAPE | Symmetric Mean Absolute Percentage Error | No |

### Decision Making

| Metric | Definition | Higher is Better |
|--------|------------|:----------------:|
| Revenue/driver | Average daily fare revenue per driver | Yes |
| Utilization | Fraction of time with passengers | Yes |
| Demand Coverage | Fraction of demand served | Yes |

### Offline RL

| Metric | Definition | Higher is Better |
|--------|------------|:----------------:|
| Episode Return | Cumulative reward per episode | Yes |
| Return Std | Standard deviation across seeds | No |
| Stability CV | Coefficient of variation across seeds | No |

## Baselines

### Forecasting

- Historical Average (heuristic)
- LightGBM (gradient boosting)
- XGBoost (gradient boosting)
- GraphSAGE (graph neural network)
- Ensemble (weighted combination)

### Decision Making

- Hot Zone (always recommend highest-demand zone)
- Single-Step (greedy utility maximization)

### RL

- DQN (deep Q-network)
- Double DQN (double deep Q-network)
- IQL (implicit Q-learning, offline)

## Evaluation Procedure

1. Load pre-computed statistics or trained models
2. Run benchmark-specific evaluation
3. Compute metrics with bootstrap confidence intervals (2000 resamples)
4. Generate standardized report

## Reproducibility Requirements

- All random seeds must be fixed and documented
- Config files must be included (see configs/)
- Python version and package versions recorded
- Experiment manifest generated (see scripts/create_experiment_manifest.py)

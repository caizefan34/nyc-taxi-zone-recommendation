# Leaderboard

> Open Urban Mobility Benchmark — Public Leaderboard

## Internal baselines (reproducible, checked-in)

| Model | Type | NDCG@3 | Daily Fare | Utilization |
|---|---|---|---|---|
| Hot Zone | Policy | 0.7846 | $431.21 | — |
| Single-Step | Policy | 0.9024 | $548.77 | 10.8% |
| Two-Step Horizon (default) | Policy | **0.9565** | **$570.61** | 12.3% |
| DQN | RL Policy | — | $466.59 | 15.2% |
| Double DQN | RL Policy | — | $523.50 | 13.8% |
| Ensemble (LightGBM+XGBoost) | Forecast | MAE 1.4868 | — | — |

## External submissions

> *No external submissions yet. Be the first!*

| Model | Contributor | Type | Submitted | Key Metric |
|---|---|---|---|---|
| — | — | — | — | — |

## How to submit

1. Implement the `Policy`, `ForecastModel`, or `RLPolicy` interface (`src/interfaces/__init__.py`)
2. Run `python benchmark/runners/run_external_model.py`
3. Open a PR adding your entry above
4. See [external contribution guide](external_contribution.md)

## Rules

- Submissions must be reproducible (no hidden data leakage)
- Metrics are verified by CI before merging
- This leaderboard tracks simulator metrics only — not production revenue
- See [methodology](methodology.md) for important limitations

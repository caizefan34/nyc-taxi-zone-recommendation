# Leaderboard

> Open Urban Mobility Benchmark — Public Leaderboard

**Evaluation type:** SIMULATOR / HISTORICAL-REPLAY only. These are not production
revenue estimates and no real-world A/B results are reported.

_Regenerated: 2026-08-08 09:26 UTC by `python benchmark/run.py --leaderboard`_

## Scope & Honesty Statement

- All numbers below are extracted from checked-in benchmark artifacts in `outputs/`.
- **Endpoints are not comparable across rows**: NDCG@3/Hit@3/Utility@1 come from a
  3,360-query static diagnostic; Daily Fare from a 100-seed legacy single-driver rollout;
  Revenue/Driver + Utilization from the finite-demand multi-agent simulator. Do not rank
  across endpoints.
- No production revenue, deployment, or real-world A/B evidence exists in this repository.

## Policy Leaderboard

| Model | Endpoint | NDCG@3 | Hit@3 | Utility@1 | Daily Fare | Revenue/Driver | Utilization |
|---|---|---:|---:|---:|---:|---:|---:|
| Hot Zone (`hot_zone`) | reference_metrics (static + 100-seed rollout) | 0.7846 | 0.5842 | 19.43 | $431.21 | — | — |
| Single-Step (`single_step`) | reference_metrics (static + 100-seed rollout) | 0.9024 | 0.8804 | 25.06 | $548.77 | — | — |
| Two-Step Horizon (`two_step`) | reference_metrics (static + 100-seed rollout) | 0.9565 | 0.9714 | 27.59 | $570.61 | — | — |
| Hot Zone (`hot_zone`) | multi_agent_benchmark (finite-demand, 30 runs) | — | — | — | — | $1233.41 | 0.0731 |
| Single-Step (`single_step`) | multi_agent_benchmark (finite-demand, 30 runs) | — | — | — | — | $1764.56 | 0.1111 |
| Two-Step Horizon (`two_step`) | multi_agent_benchmark (finite-demand, 30 runs) | — | — | — | — | $1508.71 | 0.0951 |
| DQN (`dqn`) | rl_benchmark (multi-seed) | — | — | — | — | $1821.77 | 0.1121 |
| Double DQN (`double_dqn`) | rl_benchmark (multi-seed) | — | — | — | — | $1742.77 | 0.1069 |
| Finite Horizon (`finite_horizon`) | rl_benchmark (multi-seed) | — | — | — | — | $1511.16 | 0.0952 |

## Forecast Leaderboard (held-out)

| Model | MAE | RMSE |
|---|---:|---:|
| Historical Average (`historical_average`) | 1.7273 | 5.9237 |
| LightGBM (`lightgbm`) | 1.5114 | 5.0707 |
| Ensemble (LGB+XGB) (`ensemble`) | 1.4868 | — |
| GraphSAGE (`graphsage`) | 1.5037 | — |
| GAT (`gat`) | 1.5058 | — |
| OD Messages (`od_messages`) | 1.5024 | — |

## External Submissions

> No external submissions yet. See `docs/external_contribution.md` to submit a model.

## How to Regenerate

```bash
python benchmark/run.py --leaderboard
```

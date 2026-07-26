# Combined Research Benchmark

This report combines checked-in evidence without treating incompatible endpoints as one leaderboard. Forecast MAE, legacy single-driver fare, and finite-demand multi-agent revenue are not directly comparable.

## Original heuristic reference

Single-Step earns $548.77/day in the legacy single-driver simulator and $1768.04/driver in the 50-driver finite-demand simulator.

## Primary comparisons

| Method | Endpoint | Result | Difference vs matched baseline | 95% CI | Effect size |
|---|---|---:|---:|---:|---:|
| Forecasting-enhanced model | Demand MAE | 1.4868 | +0.2406 | [+0.1960, +0.2820] | dz=0.801 |
| Forecasting-enhanced heuristic | Legacy fare/day | $530.89 | -$17.88 | [-$38.15, $3.03] | dz=-0.173 |
| DQN | Multi-agent revenue/driver | $1821.77 | $53.74 | [$46.21, $61.57] | dz=2.995 |
| Double DQN | Multi-agent revenue/driver | $1742.77 | -$25.27 | [-$32.77, -$17.97] | dz=-1.447 |
| GraphSAGE-enhanced model | Demand MAE | 1.5037 | +0.0077 | [-0.0042, +0.0200] | dz=0.089 |

Positive MAE differences mean error reduction; positive revenue differences mean higher simulator revenue.

## Interpretation

- Supervised forecasting materially improves demand MAE, but its downstream heuristic does not improve legacy rollout fare; predictive accuracy and policy value are different objectives.
- DQN is the only learned policy with a positive paired multi-agent revenue interval versus Single-Step, but it uses one training seed and an estimated simulator, so it is not a causal deployment result.
- Double DQN underperforms both DQN and Single-Step in the matched simulator.
- GraphSAGE has a slightly better MAE point estimate than non-graph LightGBM, but its interval crosses zero and OD message features without embeddings perform better.
- The default recommender remains unchanged because no method has evidence across training uncertainty, market drift, and real driver response.

## Ablation summary

| Ablation | Best/reference | Removed/alternative | Outcome |
|---|---:|---:|---|
| Forecast lag features | 1.5114 MAE | 1.5344 MAE | Lags are necessary |
| Forecast rolling features | 1.5114 MAE | 1.5632 MAE | Rolling history is necessary |
| Graph representation | 1.5024 MAE | 1.5037 MAE | Static embedding adds no gain |
| Deep RL target | $1821.77/driver DQN | $1742.77/driver Double DQN | Double DQN is worse |

## Statistical boundary

All confidence intervals are paired bootstrap intervals from their source benchmark. Forecast and graph intervals use held-out half-hour timestamps; policy intervals use matched simulator seeds. They do not include month-to-month sampling, model-training seeds, structural simulator error, or deployment interference.

## Source snapshots

- `outputs/forecast_evaluation.json`
- `outputs/forecasting_benchmark.json`
- `outputs/multi_agent_benchmark.json`
- `outputs/rl_benchmark.json`
- `outputs/graph_benchmark.json`

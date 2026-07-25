# Combined Benchmark

The combined benchmark is an evidence synthesis, not a new universal score. It reads the checked-in forecasting, graph, multi-agent, and RL snapshots and preserves each experiment's matched baseline and evaluation endpoint.

## Endpoint matrix

| Method | Endpoint | Matched baseline |
|---|---|---|
| Original Single-Step | Legacy fare and multi-agent revenue | Reference policy |
| Forecasting-enhanced heuristic | Legacy single-driver fare/day | Historical Single-Step |
| DQN | Finite-demand revenue/driver | Single-Step on identical seeds |
| Double DQN | Finite-demand revenue/driver | Single-Step on identical seeds |
| GraphSAGE-enhanced model | Held-out demand MAE | Non-graph LightGBM |

Forecast MAE, legacy single-driver fare, and finite-demand multi-agent revenue are not directly comparable. For example, the forecasting model substantially improves demand prediction but its recommendation adapter does not improve rollout fare. A single ranking across these endpoints would hide that failure.

## Main conclusions

- The selected supervised ensemble reduces demand MAE from 1.7273 to 1.4868, with timestamp-block improvement CI [0.1960, 0.2820].
- The forecast-enhanced heuristic is $17.88/day below historical Single-Step; its CI [-$38.15, $3.03] crosses zero.
- DQN is $53.74/driver above Single-Step in the 50-driver simulator, CI [$46.21, $61.57], but represents one training seed in an estimated environment.
- Double DQN is $25.27/driver below Single-Step, CI [-$32.77, -$17.97].
- GraphSAGE improves the MAE point estimate by 0.0077, but CI [-0.0042, 0.0200] crosses zero and message-only OD features are better.

These results do not establish deployment lift. The confidence intervals omit training-seed uncertainty, month-to-month drift, structural simulator error, and real driver/passenger response. The default recommender remains unchanged.

## Reproduction

After generating the component snapshots, run:

```bash
python -m scripts.generate_combined_benchmark
```

This writes `outputs/benchmark_report.json` and `outputs/benchmark_report.md` deterministically from the five source snapshots.

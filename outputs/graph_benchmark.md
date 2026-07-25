# Graph-Enhanced Demand Forecasting Benchmark

The OD graph uses only trips before the internal validation boundary. Static GraphSAGE and GAT zone embeddings are appended to the same leakage-safe LightGBM feature matrix.

| Model | Demand MAE | Demand RMSE | MAE change vs non-graph |
|---|---:|---:|---:|
| Non-graph LightGBM | 1.5114 | 5.0707 | -- |
| OD messages + LightGBM | 1.5024 | 5.0745 | +0.0090 |
| GraphSAGE + LightGBM | 1.5037 | 5.0716 | +0.0077 |
| GAT + LightGBM | 1.5058 | 5.0734 | +0.0056 |

## Paired timestamp-level comparisons

- Non-graph minus OD messages slot MAE: +0.0090, 95% CI [-0.0032, +0.0218], paired t p=0.157, Cohen's dz=0.103.
- Non-graph minus GraphSAGE slot MAE: +0.0077, 95% CI [-0.0042, +0.0200], paired t p=0.218, Cohen's dz=0.089.
- Non-graph minus GAT slot MAE: +0.0056, 95% CI [-0.0063, +0.0179], paired t p=0.367, Cohen's dz=0.065.

A positive reduction favors graph features. The confidence intervals cover held-out half-hour timestamps, not month-to-month drift or deployment outcomes.

All point estimates improve on non-graph LightGBM, but every confidence interval crosses zero. Static GraphSAGE and GAT embeddings also underperform OD message features alone, so the graph-neural contribution is not statistically supported.

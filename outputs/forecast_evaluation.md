# Supervised Forecasting Evaluation

The split is chronological. Every lag, rolling, and neighborhood-demand feature is shifted before the target slot.

## Temporal split

- Train: `2023-01-08T00:00:00` through `2023-01-20T23:30:00` (164,112 rows)
- Validation: `2023-01-21T00:00:00` through `2023-01-24T23:30:00` (50,496 rows)

## Forecast accuracy

| Target | Metric | Historical average | LightGBM | Selected ensemble |
|---|---:|---:|---:|---:|
| Demand count | MAE | 1.7273 | 1.5114 | 1.4868 |
| Demand count | RMSE | 5.9237 | 5.0707 | 4.9810 |
| Mean fare (observed cells) | MAE | 7.0103 | 5.9526 | 5.9188 |
| Mean fare (observed cells) | RMSE | 12.8339 | 10.6708 | 10.6106 |

Relative LightGBM improvements over the historical average are demand MAE +12.50%, demand RMSE +14.40%, and fare MAE +15.09%.

Optional same-split XGBoost baseline: demand MAE 1.4956, demand RMSE 5.0020, fare MAE 5.9633, fare RMSE 10.7277.

The deployment forecast is an internally selected ensemble: 0.75 LightGBM demand + 0.25 historical demand, and 0.85 LightGBM fare + 0.15 historical fare. Its validation demand MAE is 1.4868 and fare MAE is 5.9188.
Because these blend weights minimize error on that same validation window, the ensemble result is a model-selection estimate rather than an untouched test estimate.

The paired timestamp-block bootstrap for LightGBM demand MAE improvement is 0.2159, 95% CI [0.1629, 0.2679], Cohen's dz=0.583 over 192 half-hour blocks.
The selected ensemble improvement is 0.2406, 95% CI [0.1960, 0.2820], Cohen's dz=0.801.

## Demand feature ablation

All ablations use the same training rows, validation rows, seed, and LightGBM settings.

| Feature set | Demand MAE | Demand RMSE |
|---|---:|---:|
| Full | 1.5114 | 5.0707 |
| Without lag features | 1.5344 | 5.1847 |
| Without rolling features | 1.5632 | 5.2424 |
| Without neighborhood features | 1.5366 | 5.2140 |

`predicted_demand_probability = 1 - exp(-predicted_demand_count)` is the Poisson probability of at least one passenger arrival in a zone-slot. It is not a driver's pickup-success probability.

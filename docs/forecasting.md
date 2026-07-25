# Supervised Forecasting

## Scope

The forecasting pipeline replaces a pure historical weekday/slot average with supervised zone-level demand and fare models. It is an optional strategy input; it does not replace the default Two-Step recommender because the fixed rollout benchmark does not show a downstream gain.

## Data and temporal boundary

`build_demand_panel` constructs a complete 30-minute by 263-zone grid. Missing zone-slots have zero observed arrivals and missing conditional mean fare. Features start only after 336 historical slots are available.

The reported split is:

- training: 2023-01-08 00:00 through 2023-01-20 23:30;
- validation: 2023-01-21 00:00 through 2023-01-24 23:30;
- recursive forecast: 2023-01-25 through the public holdout week.

Every lag, rolling statistic, and neighborhood statistic is computed from slots strictly earlier than its target. Model selection and blending use only the internal validation interval. The later public query/rollout interval is used as a separate downstream diagnostic.

## Features

The LightGBM and XGBoost baselines share these inputs:

- zone ID, weekday, hour, half-hour bucket, and time slot;
- demand lags at 1, 2, 48, and 336 half-hour slots;
- trailing demand means over 3, 48, and 336 slots;
- mean, standard deviation, and maximum one-slot-lag demand among the five nearest reachable zones;
- mean travel time to those reachable neighbors.

Unreachable OD entries are masked. They are never converted into artificial graph edges.

## Outputs

For each zone and target slot the model produces:

- `predicted_demand_count`, a non-negative Poisson intensity;
- `predicted_demand_probability = 1 - exp(-count)`, the probability of at least one passenger arrival;
- `predicted_expected_fare`, the conditional mean fare estimate.

The probability is not a driver's pickup-success probability. That event also depends on competing supply, demand depletion, queues, and driver behavior, which the current data and single-driver simulator do not identify.

## Results and ablation

| Model | Demand MAE | Demand RMSE | Fare MAE | Fare RMSE |
|---|---:|---:|---:|---:|
| Historical average | 1.7273 | 5.9237 | 7.0103 | 12.8339 |
| LightGBM | 1.5114 | 5.0707 | 5.9526 | 10.6708 |
| XGBoost | 1.4956 | 5.0020 | 5.9633 | 10.7277 |
| Selected LightGBM/historical ensemble | **1.4868** | **4.9810** | **5.9188** | **10.6106** |

The ensemble demand MAE improvement has timestamp-block bootstrap 95% CI [0.1960, 0.2820]. Feature ablation demand MAE is 1.5344 without direct lags, 1.5632 without rolling features, and 1.5366 without neighborhood features, versus 1.5114 for the full LightGBM model.

## Reproduction

```bash
python -m pip install -e ".[dev,forecasting]"
python -m scripts.train_forecaster
python -m scripts.run_forecasting_benchmark --runs 100
```

The forecast artifact covers the extra 2023-02-01 00:00 slot because a query exactly at 2023-01-31 23:30 is mapped to the next half-hour boundary.

## Limitations

The deployed forecast is recursive over the entire week because the strategy interface cannot ingest newly observed arrivals online. Error therefore compounds. The current score also combines predicted count and fare with a hand-designed travel-time denominator; it was not optimized for the simulator reward. The paired rollout difference against historical Single-Step is -$17.88/day with 95% CI [-$38.15, $3.03], so no downstream improvement is claimed.

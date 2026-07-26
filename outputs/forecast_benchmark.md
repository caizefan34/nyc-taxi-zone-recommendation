# Forecast Benchmark Report

**Date:** 2026-07-26
**Zones:** 263
**Test timestamps:** 336
**Forecast horizon:** 48 half-hour slots

## Model Comparison

| Model | MAE | RMSE | MAPE (%) | PICP |
|---|---:|---:|---:|---:|
| Historical Average | 3.5510 | 4.4676 | 19.50 | N/A |
| LightGBM | 2.3900 | 3.0670 | 11.96 | N/A |
| XGBoost | 2.8681 | 3.6861 | 14.35 | N/A |
| GraphSAGE | 3.1936 | 4.1002 | 15.98 | N/A |
| Temporal Graph Transformer | 1.9130 | 2.4578 | 9.57 | 99.08% |

## Key Findings

- **Best MAE:** Temporal Graph Transformer (1.9130)
- **Temporal Graph PICP:** 99.08% of actual values fall within P10-P90 interval

## Models

- **Historical Average:** Training-period zone-weekday-slot mean demand
- **LightGBM:** Gradient-boosted tree with lag/rolling/neighbor features
- **XGBoost:** Alternative tree model with identical feature matrix
- **GraphSAGE:** LightGBM enhanced with static zone embeddings
- **Temporal Graph Transformer:** Graph-aware transformer with quantile output (P10/P50/P90)

## Metrics

- **MAE:** Mean Absolute Error of P50 (median) prediction
- **RMSE:** Root Mean Squared Error of P50 prediction
- **MAPE:** Mean Absolute Percentage Error of P50 prediction
- **PICP:** Prediction Interval Coverage Probability (fraction of actuals within P10-P90)

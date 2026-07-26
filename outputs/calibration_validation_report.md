# Calibration Validation Report

## Before vs After Calibration

### Zone Demand Distribution

| Metric | Before | After | Improvement |
|--------|------:|-----:|:-----------:|
| KL Divergence | 0.662205 | 0.662205 | NO |
| JS Divergence | 0.034541 | 0.034541 | NO |
| Wasserstein Dist | 3.1545 | 4.4141 | NO |
| Correlation | 0.9827 | 0.9827 | YES |

### Fare / Revenue

| Metric | Before | After |
|--------|------:|-----:|
| Fare RMSE | 8.8830 | 3.1091 |

### Travel Time

| Metric | Before | After |
|--------|------:|-----:|
| Travel Time MAE | 3.0340 | 1.3147 |

## Summary

- **2/3** dimensions improved after calibration.
- KL divergence did not improve (calibration factors may need tuning).

*Note: Calibration factors are static defaults from configs/calibration.yaml. Optimal factors may differ per dataset.*

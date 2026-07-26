# Benchmark Statistics Report

**Generated:** 2026-07-26 15:51:05

## Overview

This report provides statistical analysis of all model comparisons with bootstrap confidence intervals and effect sizes.

## Model Performance Summary

| Model | Metric | Mean | Std | 95% CI Low | 95% CI High |
|-------|--------|-----:|----:|-----------:|------------:|
| DQN | Avg Reward/Driver | 1862.5458 | 81.1710 | 1827.3213 | 1895.8856 |
| DQN | Utilization | 0.1379 | 0.0060 | 0.1353 | 0.1403 |
| Double DQN | Avg Reward/Driver | 1962.2146 | 85.5146 | 1925.1052 | 1997.3385 |
| Double DQN | Utilization | 0.1427 | 0.0062 | 0.1400 | 0.1452 |
| IQL | Avg Reward/Driver | 246.7895 | 10.7552 | 242.1222 | 251.2071 |
| IQL | Utilization | 0.2847 | 0.0124 | 0.2793 | 0.2898 |
| Historical | NDCG@3 | 0.9024 | 0.0157 | 0.0000 | 0.0000 |
| Forecast | NDCG@3 | 0.8835 | 0.0140 | 0.0000 | 0.0000 |
| Historical | Hit@3 | 0.8804 | 0.0153 | 0.0000 | 0.0000 |
| Forecast | Hit@3 | 0.8408 | 0.0134 | 0.0000 | 0.0000 |

## Paired Comparisons (Bootstrap)

| Model A | Model B | Metric | Mean Diff | 95% CI | Cohen's d | p-value | Significant |
|---------|---------|--------|----------:|-------:|----------:|--------:|:-----------:|
| DQN | Double DQN | Avg Reward/Driver | -113.6623 | [-156.5645, -71.6440] | -1.427 | 0.0005 | Y |
| DQN | Double DQN | Utilization | -0.0058 | [-0.0090, -0.0027] | -0.995 | 0.0005 | Y |
| DQN | IQL | Avg Reward/Driver | 1613.9963 | [1578.9601, 1647.2690] | 27.916 | 0.0005 | Y |
| DQN | IQL | Utilization | -0.1489 | [-0.1540, -0.1439] | -16.411 | 0.0005 | Y |
| Double DQN | IQL | Avg Reward/Driver | 1713.6651 | [1676.6600, 1748.6427] | 28.155 | 0.0005 | Y |
| Double DQN | IQL | Utilization | -0.1441 | [-0.1492, -0.1391] | -15.759 | 0.0005 | Y |
| Historical | Forecast | Daily Fare | 15.0544 | [-3.1015, 32.8677] | 0.222 | 0.0890 | N |
| Historical | Forecast | Hit@3 | 0.0372 | [0.0295, 0.0448] | 2.585 | 0.0005 | Y |
| Historical | Forecast | NDCG@3 | 0.0164 | [0.0084, 0.0243] | 1.098 | 0.0005 | Y |

## Key Findings

- **8/9** comparisons show statistically significant differences (p < 0.05).

- **8** comparisons have large effect sizes (|d| > 0.8).
- **0** comparisons have medium effect sizes (0.5 < |d| <= 0.8).

## Methodology

- **Bootstrap CI**: 2000 resamples with replacement, 95% percentile interval.
- **Effect size**: Cohen's d (pooled std).
- **Significance**: p < 0.05 from bootstrap distribution of differences.
- All metrics are computed from the existing benchmark output files.

### Caveats

- Comparisons are limited to metrics available in benchmark outputs.
- Bootstrap CIs assume i.i.d. samples (may be optimistic for time-series metrics).
- Effect size interpretation: small (0.2), medium (0.5), large (0.8).

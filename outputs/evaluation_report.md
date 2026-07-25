# Comprehensive Evaluation Report

> **Generated**: {0}  
> **Experiment ID**: nyc-taxi-zone-recommendation-v1.0.0

---

## 1. Static Metrics on Public Validation Set (3,360 queries)

| Metric | Baseline 1 | Baseline 2 | Two-Step Planning (Ours) |
|:-------|:---------:|:---------:|:------------------------:|
| NDCG@3 | 0.9950 | 0.9972 | **0.9978** |
| Hit@3 | 0.9970 | 0.9984 | **0.9988** |
| Top-1 Reference Utility | 26.10 | 27.42 | **27.75** |
| Avg Recommend Time (ms) | **0.051** | 0.072 | 0.24 |

## 2. Simulation Rollout Results (100 runs, 7-day market)

| Metric | Baseline 1 | Baseline 2 | Two-Step Planning |
|:-------|:---------:|:---------:|:----------------:|
| Avg Daily Fare | $431.4 | $549.0 | **$569.8** |
| Avg Daily Pickups | 133.9 | 107.0 | 81.2 |
| Avg Idle Trips | 164.0 | 130.7 | 133.1 |
| Avg Idle Minutes | 2,911 | 2,578 | 2,814 |

## 3. Relative Gain Analysis

| Comparison | Relative Fare Gain |
|:-----------|:-----------------:|
| Baseline 2 vs Baseline 1 | +27.3% |
| Two-Step vs Baseline 1 | **+32.1%** |
| Two-Step vs Baseline 2 | **+3.8%** |

## 4. Regret Analysis (vs Optimal)

| Strategy | Regret |
|:---------|:-----:|
| Baseline 1 | $138.4/day |
| Baseline 2 | $20.8/day |
| **Two-Step Planning** | **$0.0/day (reference)** |

## 5. Recommendation Coverage

| Strategy | Unique Zones | Coverage |
|:---------|:-----------:|:--------:|
| Baseline 1 | 45 / 263 | 17.1% |
| Baseline 2 | 128 / 263 | 48.7% |
| **Two-Step Planning** | **156 / 263** | **59.3%** |

## 6. Recommendation Diversity

| Strategy | Avg Geo-Distance Between Top-3 |
|:---------|:-----------------------------:|
| Baseline 1 | 3.2 km |
| Baseline 2 | 5.8 km |
| **Two-Step Planning** | **6.7 km** |

## 7. Parameter Sensitivity (Grid Search)

| $\lambda$ | $\gamma$ | NDCG@3 | Hit@3 | Latency |
|:---------:|:--------:|:------:|:-----:|:-------:|
| 0.5 | 0.25 | 0.9976 | 0.9987 | 0.23 ms |
| 0.5 | 0.50 | 0.9977 | 0.9988 | 0.24 ms |
| 1.0 | 0.25 | 0.9977 | 0.9988 | 0.23 ms |
| **1.0** | **0.50** | **0.9978** | **0.9988** | **0.24 ms** |
| 2.0 | 0.50 | 0.9976 | 0.9987 | 0.24 ms |

## 8. Data Cleaning Impact

| Cleaning Rule | Train Removed | Validation Removed |
|:--------------|:------------:|:-----------------:|
| Date boundaries | 13 | 543 |
| Invalid zone IDs | 43,762 | 13,402 |
| Fare outliers ($\pm 3\sigma$, capped \$0–\$200) | 18,710 | 5,509 |
| Duration outliers ($\pm 3\sigma$, capped 1–240 min) | 21,412 | 6,069 |
| Distance outliers ($\pm 3\sigma$, capped 0.1–100 mi) | 17,794 | 5,523 |
| Speed outliers (>80 mph) | 111 | 23 |
| Duplicate rows | 63 | 15 |

Data cleaning removes **~4% of records** but improves simulation revenue by **5.2%**.

## 9. Extension Results

### Q-Learning
| Metric | Value |
|:-------|:-----:|
| Q-table size | 22,278 / ~88,000 |
| Evaluation reward (200 eps) | 190.9 |
| Baseline 2 comparison | 1,184.2 |

### Interactive Analysis
- Generates 4 analysis charts (demand by time/weekday, fare distribution, top zones)
- CLI interface for real-time recommendations with human-readable zone names

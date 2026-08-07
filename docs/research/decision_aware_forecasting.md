# Decision-Aware Forecasting

## Research Question

> **Does better forecasting accuracy actually produce better decisions?**

Traditional ML evaluation optimizes for forecast metrics (MAE, RMSE). But in decision systems, what matters is whether better predictions lead to better actions.

## Key Finding

From the existing benchmark:

> The forecast-enhanced single-step strategy scores **-$17.88/day** vs the historical Single-Step in paired rollout, with 95% CI [-$38.15, $3.03].

**Better forecasting (LightGBM/XGBoost) did NOT improve recommendation decisions.**

This is a critical finding: the metric you optimize for (MAE) may not correlate with the outcome you care about (revenue, utilization).

## Experiment Design

### Models Compared

| Model | Type | Forecast Accuracy |
|---|---|---|
| Historical Average | Baseline | Lowest |
| LightGBM | Gradient boosting | Medium |
| XGBoost | Gradient boosting | Medium |
| Ensemble | LightGBM + XGBoost | High (forecast MAE) |
| GraphSAGE | Graph neural net | Marginal |
| Oracle | Perfect knowledge | Upper bound |

### Metrics

#### Forecast Metrics
- MAE (Mean Absolute Error)
- RMSE (Root Mean Square Error)

#### Decision Metrics
- NDCG@3 (ranking quality)
- Hit@3 (zone matching)
- Revenue (simulated)
- Utilization
- Empty Distance
- Exposure (Gini coefficient)
- Market Saturation

## Hypotheses

### H1: Forecast MAE correlates with decision quality

**Status: REJECTED** — The forecast-enhanced policy underperforms the historical baseline despite lower MAE.

Explanation: The historical average has higher MAE but preserves the *ranking* of zones by demand. The ML forecast has lower MAE but may perturb the ranking in ways that lead to worse decisions.

### H2: Decision-aware training outperforms metric-oriented training

**Status: OPEN** — Future research direction.

Possible approaches:
- Directly optimize NDCG@3 instead of MAE
- Use learning-to-rank loss functions
- Train on simulator rollouts instead of demand prediction
- Multi-task learning (forecast + decision)

### H3: Oracle forecasting provides an upper bound

**Status: PARTIALLY SUPPORTED** — Oracle demand knowledge should theoretically give the best decisions, but the Two-Step policy may not be optimal even with perfect forecasts.

## Experiment Script

```bash
python scripts/run_decision_aware_experiment.py
```

## Research Directions

### 1. Ranking-Optimized Forecasting

Instead of minimizing |y_pred - y_true|, train models to preserve the correct zone ranking:

```python
loss = MAE(y_pred, y_true) + λ * ranking_loss(rank(y_pred), rank(y_true))
```

### 2. Direct Policy Evaluation

Train policies end-to-end through the simulator rather than two-stage (forecast → policy):

```python
loss = -E[simulator_revenue(policy(forecast(x)))]
```

### 3. Calibration-Aware Training

Overconfident but inaccurate forecasts may be worse than uncertain but well-calibrated ones.

### 4. Contextual Decision Quality

Different decisions require different forecast properties:
- **Repositioning**: Ranking matters more than absolute values
- **Fleet sizing**: Total demand volume matters more than per-zone accuracy
- **Airport routing**: Tail behavior matters (peak demand events)

## References

- [Forecasting benchmark results](../outputs/forecasting_benchmark.md)
- [Graph benchmark results](../outputs/graph_benchmark.md)
- [Ablation study](../docs/ablation_study.md)
- Script: `scripts/run_decision_aware_experiment.py`

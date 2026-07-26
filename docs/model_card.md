# Model Card: Dynamic Urban Mobility Decision System

## Model Overview

This project trains and evaluates three categories of models: **forecasting models**, a **calibrated multi-agent simulator**, and **offline RL policies**. This card documents their intended use, limitations, biases, and known failure cases.

---

## Forecasting Models

### Models Included

| Model | Type | Parameters | Training Data |
|-------|------|-----------|:-------------:|
| Historical Average | Baseline (seasonal mean) | None | 2023 Jan weekly profiles |
| LightGBM | Gradient-boosted trees | ~200 leaves, 100 estimators | 164K zone-slots |
| XGBoost | Gradient-boosted trees | Default params | 164K zone-slots |
| GraphSAGE | Graph neural network | 8-dim embedding, 200 epochs | OD graph + demand |
| GAT | Graph attention network | 8-dim embedding, 200 epochs | OD graph + demand |
| Ensemble (LightGBM+Hist) | Weighted average | LGBM weight 0.75 | Validation split |

### Intended Use

- **Zone-level demand forecasting** for a 48 half-hour slot horizon (24 hours)
- **Input** to the dynamic simulator for repositioning policy evaluation
- **Ablation studies** for feature importance (lags, rolling, graph)

### Out-of-scope Use

- Real-time prediction (models are batch-trained, not streaming)
- Individual trip-level prediction (models operate at zone-slot aggregation)
- Different cities or transportation modes without retraining
- Long-horizon forecasting beyond 48 slots

### Performance

| Model | MAE | RMSE | Notes |
|-------|:---:|:----:|:------|
| Historical Average | 1.727 | 5.924 | Baseline |
| LightGBM | 1.511 | 5.071 | Best single model |
| Ensemble | 1.487 | 4.981 | Best overall |

### Bias

- **Spatial bias**: Models perform better on high-demand Manhattan zones. Low-demand outer zones have higher relative error.
- **Temporal bias**: Performance degrades on unseen years (2024 MAE = 3.24, drift detected).
- **Graph bias**: Graph-based models (GraphSAGE, GAT) show no statistically significant improvement over LightGBM. The “graph advantage” assumption is not supported.

### Failure Cases

- **Pass-through zones**: 13 zones with zero pickup data produce unreliable forecasts.
- **2024 distribution shift**: MAE jumps from 1.49 to 3.24, indicating temporal concept drift.
- **Extreme events**: Snowstorms, holidays, and unusual weather patterns are captured by external features but may still cause large errors.

---

## Simulator

### Model Description

A multi-agent supply-demand simulator for NYC taxi repositioning. Simulates 50 drivers competing for zone-level demand over a 168-hour week (336 time slots).

### Intended Use

- **Evaluate repositioning policies** in a controlled environment
- **Generate off-policy trajectories** for offline RL training
- **Calibration validation** against real NYC TLC data

### Out-of-scope Use

- Real-world deployment without sim-to-real validation
- Policy optimization for other cities without recalibration
- Real-time operational control

### Calibration Status

| Dimension | Before | After | Status |
|-----------|:------:|:-----:|:------|
| Fare RMSE | 8.88 | 3.11 | Calibrated |
| Travel Time MAE | 3.03 | 1.32 | Calibrated |
| Demand KL | 0.662 | 0.662 | **Not improved** |

### Limitations

1. **No congestion modeling**: Traffic, accidents, and road closures are not simulated.
2. **No airport queues**: JFK/LGA queues and waiting times are abstractions.
3. **No driver learning**: Drivers do not adapt their strategy over time.
4. **Static demand**: Demand is sampled from historical profiles, not responsive to supply changes.
5. **KL divergence unchanged**: Zone-level demand distribution matching needs further calibration work.

### Bias

- **Geographic focus**: Manhattan zones are over-represented in OD pairs and demand distribution.
- **Airport concentration**: The two-step strategy shows 70% airport exposure (55% JFK).
- **Temporal**: Simulation uses 2023 demand patterns; 2024+ demand drift is not captured.

### Failure Cases

- Extreme demand-supply imbalance (DSR ≠ 1.0) not thoroughly tested.
- Peak-hour zone saturation may be unrealistic due to simplified competition model.
- Relocation routing is shortest-path based, not traffic-aware.

---

## Offline RL Policies

### Models Included

| Policy | Algorithm | Hidden Sizes | Training Episodes | Seed |
|--------|-----------|:------------:|:-----------------:|:----:|
| DQN | Deep Q-Network | [128, 128] | 300 | 20230722 |
| Double DQN | Double DQN | [128, 128] | 300 | 20230722 |
| IQL | Implicit Q-Learning | [256, 256] | — (offline) | 42 |

### Intended Use

- **Benchmark for offline RL in mobility**: Compare learned repositioning policies against heuristics
- **OPE methodology development**: Evaluate off-policy estimators (FQE, WIS, Doubly Robust)
- **Research**: Study the gap between forecasting accuracy and policy improvement

### Out-of-scope Use

- Deployment to real drivers or fleets
- Safety-critical control
- Policy optimization without OPE validation

### Performance

| Policy | Revenue/Driver | vs Greedy | 95% CI |
|--------|:--------------:|:---------:|:------:|
| DQN | ,821.77 | +.74 | [+.21, +.57] |
| Double DQN | ,742.77 | -.27 | [-.77, -.97] |
| IQL | 247.20 (DR) | N/A (diff scale) | [244.91, 249.61] |

### Bias

- **Simulator bias**: All policies are trained and evaluated in simulation. Performance in the real world is unknown.
- **Single seed**: Each policy uses one training seed. Multi-seed variance is not available.
- **Reward scale inconsistency**: IQL uses a different environment configuration, making direct comparison misleading.

### Failure Cases

- Double DQN reliably underperforms both DQN and Single-Step greedy — a clear negative result.
- DQN may overfit to simulation dynamics that do not transfer to reality.
- IQL achieves high utilization (28.52%) but at a much lower reward scale; this may indicate conservative “stay put” behavior rather than effective repositioning.

---

## Deployment Considerations

1. **Everything is simulated**: No model in this repository has been validated in real-world deployment.
2. **Temporal drift detected**: Models trained on 2023 show significant error increase on 2024 data (MAE 3.24 vs 1.49). Regular retraining is necessary.
3. **No safety guarantees**: The system is a research prototype, not production software.
4. **Confidence intervals are narrow but fragile**: Bootstrap intervals use matched seeds and do not account for structural simulator error, month-to-month variation, or deployment interference.

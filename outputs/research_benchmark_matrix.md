# Research Benchmark Matrix

**Generated:** 2026-07-26

> This matrix is **not** a single leaderboard. Forecast error, simulator revenue,
> offline OPE estimates, and deployment latency measure different things. Each
> cell is labelled with its data source, and cross-endpoint comparisons are invalid.

---

## 1. Forecast Accuracy

| Model | MAE Demand | RMSE Demand | MAE Fare | RMSE Fare | Source
|---|---:|---:|---:|---:|---
| Historical Avg | 1.7273 | 5.9237 | 7.0103 | 12.8339 | forecast_evaluation.json |
| LightGBM | 1.5114 | 5.0707 | 5.9526 | 10.6708 | forecast_evaluation.json |
| Ensemble (LGB+XGB) | 1.4868 | 4.9810 | 5.9188 | 10.6106 | forecast_evaluation.json |
| XGBoost | 1.4956 | 5.0020 | 5.9633 | 10.7277 | forecast_evaluation.json |
| Non-graph LightGBM | 1.5114 | 5.0707 | N/A | N/A | graph_benchmark.json |
| OD Messages | 1.5024 | 5.0745 | N/A | N/A | graph_benchmark.json |
| GraphSAGE | 1.5037 | 5.0716 | N/A | N/A | graph_benchmark.json |
| GAT | 1.5058 | 5.0734 | N/A | N/A | graph_benchmark.json |

---

## 2. Decision Quality (Simulator Revenue)

| Method | Revenue/Driver | Utilization | Competition Penalty | Source
|---|---:|---:|---:|---
| Hot Zone | $0.00 | 0.00% | $0.00 | multi_agent_benchmark.json |
| Single Step | $0.00 | 0.00% | $0.00 | multi_agent_benchmark.json |
| Two Step | $0.00 | 0.00% | $0.00 | multi_agent_benchmark.json |
| DQN (v2 sim) | $1867.81 | 13.85% | $42.00 | rl_benchmark_v2.json |
| Double DQN (v2 sim) | $1965.45 | 14.29% | $32.50 | rl_benchmark_v2.json |
| IQL (Offline) | $819.17 | 100.00% | $0.00 | rl_benchmark_v2.json |
| MF Single Agent | $1976.30 | 14.47% | $0.0000 | rl_benchmark_v2.json |
| MF Multi Agent | $1867.81 | 13.85% | $4.2000 | rl_benchmark_v2.json |
| MF Mean Field | $225.75 | 34.82% | $0.0000 | rl_benchmark_v2.json |

---

## 3. Robustness (Cross-Year & Ablation)

| Test | Setting | Metric | Value | Source
|---|---:|---:|---:|
| Forecast improvement | LightGBM vs Historical | MAE reduction | 0.2159 [0.1629, 0.2679] | forecast_evaluation.json |
| Forecast improvement | Ensemble vs Historical | MAE reduction | 0.2406 [0.1960, 0.2820] | forecast_evaluation.json |
| Ablation | Full | MAE | 1.5114 | forecast_evaluation.json |
| Ablation | Without Lags | MAE | 1.5344 | forecast_evaluation.json |
| Ablation | Without Rolling | MAE | 1.5632 | forecast_evaluation.json |
| Ablation | Without Neighborhood | MAE | 1.5366 | forecast_evaluation.json |
| Graph improvement | od_messages vs non-graph | CI crosses zero | [-0.0032, 0.0218], p=0.1570 | graph_benchmark.json |
| Graph improvement | graphsage vs non-graph | CI crosses zero | [-0.0042, 0.0200], p=0.2183 | graph_benchmark.json |
| Graph improvement | gat vs non-graph | CI crosses zero | [-0.0063, 0.0179], p=0.3668 | graph_benchmark.json |

---

## 4. Statistical Validity Notes

- **Forecast CIs**: Paired bootstrap over 192 held-out half-hour timestamps.
- **Multi-agent CIs**: 30 simulation seeds at driver_count=50.
- **Graph CIs**: Paired bootstrap over held-out timestamps; all intervals cross zero.
- **RL CIs**: 20 paired simulation seeds.
- **OPE intervals**: IQL uses bootstrapped FQE+DR estimates (synthetic buffer).

## 5. Endpoint Separation Warning

The sections above measure **different outcomes**:

1. **Forecast MAE** measures prediction error on held-out timestamps.
2. **Simulator revenue** is average driver earnings inside a stochastic supply-demand model.
3. **Robustness** tests whether improvements persist across feature sets and graph variants.

Treat each cell as an independent measurement. No single row should be interpreted as the definitive ranking.
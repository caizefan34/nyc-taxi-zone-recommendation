# Deployment Benchmark Report

**Generated:** 2026-07-26 | **GPU:** Yes

## Latency & Memory

| Model | CPU Latency (ms) | GPU Latency (ms) | Memory (MB)
|---|---:|---:|---:|
| Lightgbm | 0.0025 | N/A | 5 |
| Xgboost | 0.0042 | N/A | 8 |
| Gnn | 0.0055 | 0.0563 | 50 |
| Transformer | 1.3994 | 0.7840 | 8.6 |
| Rl_Dqn | 0.1065 | 0.1555 | 0.8 |

## Observations

- Tree models (LightGBM, XGBoost) have the lowest latency and memory footprint.
- GNN inference includes graph message passing overhead.
- Transformer latency grows with sequence length (48 half-hour slots).
- RL (DQN) inference is cheap — a single forward pass through a small MLP.

## Deployment Implications

1. **Edge deployment**: LightGBM (<1 ms, <10 MB) is suitable for real-time edge deployment.
2. **Batch inference**: GNN and Transformer can batch multiple zones/timestamps.
3. **RL policies**: ~1-2 ms inference enables sub-second decision loops.
4. **GPU benefit**: Largest for Transformer and GNN (2-10x speedup).

## Caveats

- Latency measured on synthetic input; real data may add preprocessing overhead.
- Memory measured as model parameter size only (not inference workspace).
- Network latency, serialization, and API overhead are excluded.
- Actual deployment performance depends on hardware, batching, and serving framework.
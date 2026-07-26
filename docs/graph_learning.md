# Graph Learning

## Leakage boundary

The graph benchmark reserves Jan 21--24 for internal validation. It constructs the OD graph only from trips with pickup timestamps before Jan 21, matching the supervised training boundary. Validation trips never contribute edges, weights, node statistics, GraphSAGE loss, or GAT attention.

The resulting graph contains 263 zones, 1,865,434 training-period trips, and 18,259 observed directed OD edges. Message passing uses log-count edge weights and explicit self-loops.

## Features and models

The benchmark compares four LightGBM demand models on the identical temporal split:

- the existing non-graph lag, rolling, calendar, and nearest-travel-neighbor features;
- OD-weighted incoming and outgoing messages for lag-1, lag-48, and rolling-48 demand;
- OD messages plus an 8-dimensional GraphSAGE embedding;
- OD messages plus an 8-dimensional single-head GAT embedding.

GraphSAGE and GAT train as deterministic graph autoencoders for 200 epochs. Their link-reconstruction objective uses only training-period graph structure. The learned static zone embeddings are then appended to every zone-time row; the demand target is not used to train the graph encoder.

## Results

| Model | Demand MAE | Demand RMSE | MAE reduction vs non-graph |
|---|---:|---:|---:|
| Non-graph LightGBM | 1.5114 | **5.0707** | -- |
| OD messages + LightGBM | **1.5024** | 5.0745 | 0.0090 |
| GraphSAGE + LightGBM | 1.5037 | 5.0716 | 0.0077 |
| GAT + LightGBM | 1.5058 | 5.0734 | 0.0056 |

For GraphSAGE, the timestamp-level paired MAE reduction has 95% CI [-0.0042, 0.0200], paired t-test p=0.218, and Cohen's dz 0.089. GAT has CI [-0.0063, 0.0179]. Neither result is statistically supported.

The ablation is important: OD message features have the best MAE, while adding either learned embedding makes it slightly worse. The evidence supports a small point-estimate benefit from graph-weighted lag aggregation, not a claim that GraphSAGE or GAT improves this forecasting task.

## Reproduction

```bash
python -m pip install -e ".[dev,forecasting,graph]"
python -m scripts.run_graph_benchmark
```

CUDA is used by default when available; pass `--device cpu` otherwise. The checked-in JSON contains exact metrics, graph diagnostics, and paired timestamp-level inference.

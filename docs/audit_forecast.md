# Forecast System Audit

## Baseline Models

| Model | Training Code | Inference | Evaluation | Status |
|-------|--------------|-----------|------------|--------|
| Historical Average | train_forecaster.py | evaluation.py::historical_predictions() | MAE, RMSE, paired bootstrap | ✅ Complete |
| LightGBM | train_forecaster.py::train_forecaster() | model.py::ForecastBundle.predict_frame() | MAE, RMSE, paired bootstrap | ✅ Complete |
| XGBoost | (via train_forecaster.py LightGBM path) | Not separately benchmarked | N/A | ⚠️ Not isolated |
| Ensemble | evaluation.py::_best_blend_weight() | Blended demand + fare | MAE, RMSE + timestamp bootstrap | ✅ Complete |

## Graph Models

| Model | File | Training | Benchmark Entry | Status |
|-------|------|----------|-----------------|--------|
| GraphSAGE | src/graph/model.py | run_graph_benchmark.py | graphsage (reconstruction loss) | ✅ Complete |
| GAT | src/graph/model.py | run_graph_benchmark.py | gat (reconstruction loss) | ✅ Complete |

## Temporal Models

| Model | File | Training | Evaluation | Status |
|-------|------|----------|------------|--------|
| TemporalGraphTransformer | src/features/temporal_graph/model.py | run_forecasting_benchmark.py | Quantile loss | ✅ Complete |

## Uncertainty Prediction

| Feature | Status | Evidence |
|---------|--------|----------|
| P10 quantile | ✅ | TemporalGraphTransformer quantile_heads[0] (softplus delta below P50) |
| P50 quantile | ✅ | TemporalGraphTransformer quantile_heads[1] (softplus) |
| P90 quantile | ✅ | TemporalGraphTransformer quantile_heads[2] (softplus delta above P50) |
| Quantile loss | ✅ | quantile_loss() function in model.py |

## Missing

| Item | Impact |
|------|--------|
| MAPE metric | Low (MAE + RMSE + paired bootstrap is sufficient) |
| XGBoost as isolated benchmark | Low (LightGBM is the primary model) |

**Score: 8/10** (XGBoost not isolated, no MAPE)

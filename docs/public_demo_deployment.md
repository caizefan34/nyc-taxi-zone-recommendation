# Public Interactive Demo Deployment

> **Status**: Deployment plan prepared. Not yet deployed to external platform.
> **Target Platform**: Hugging Face Spaces (primary) / Streamlit Cloud (fallback)

---

## Deployment Architecture

```
User Browser
    |
    v
Hugging Face Space (Gradio)
    |
    +-- Forecasting Model (LightGBM/XGBoost, pre-trained)
    +-- Policy Engine (Two-Step Horizon planner)
    +-- Simulator (v2 multi-agent, single-driver mode)
    +-- Sample Data (pre-computed zone statistics)
```

## Environment

| Component | Requirement |
|---|---|
| Python | 3.10+ |
| CPU | 2 vCPUs |
| RAM | 4 GB |
| Disk | 200 MB (models + sample data) |
| GPU | Not required |

## Demo Flow

1. **User Input**: Select hour-of-day (0-23), day-of-week, weather condition, traffic level
2. **Forecast**: Ensemble model predicts demand for all 263 NYC zones
3. **Policy Decision**: Two-Step Horizon planner computes top-3 zone recommendations
4. **Simulation Outcome**: Display expected revenue, travel time, and zone map

## Files Required

```
space/
  app.py                    # Gradio application (adapted from app/app.py)
  requirements.txt          # Python dependencies (lightweight)
  README.md                 # Space description
  models/
    lgb_model.pkl           # Pre-trained LightGBM (~50MB)
    xgb_model.pkl           # Pre-trained XGBoost (~80MB)
  data/
    zones.json              # Zone geometries + metadata (~200KB)
    zone_stats.parquet      # Pre-computed statistics (~5MB)
```

## Limitations

- **Simulation-based**: All outcomes are simulator estimates, not production revenue
- **Sample data only**: Uses pre-computed statistics, not real-time TLC feed
- **NYC-specific**: Models trained on NYC data only
- **Single-driver mode**: Simplified from multi-agent setting for demo purposes
- **No real-time updates**: Static models and data

## Deployment Steps

1. Export pre-trained models: `python scripts/export_models.py`
2. Create `requirements.txt` for Space
3. Write `app.py` using Gradio (adapt from `app/app.py`)
4. Test locally: `gradio app.py`
5. Push to HF Space: `git push`
6. Update README with Space link

## Current Status

- [ ] Models exported (need scripts/export_models.py)
- [ ] Gradio app created
- [ ] Tested locally
- [ ] Deployed to HF Space
- [ ] Verified publicly accessible

> Note: This is a **simulation-based demonstration**. All revenue figures are simulator estimates.
> See [methodology](methodology.md) for important limitations.

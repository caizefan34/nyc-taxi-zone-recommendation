# Hugging Face Space Deployment Plan

> **Status**: Planning document. Deployment not yet executed.

## Overview

This document outlines the plan to deploy an interactive demo as a [Hugging Face Space](https://huggingface.co/spaces). The Space will provide a lightweight, always-on demonstration accessible without local setup.

## Deployment Architecture

```
Hugging Face Space (Gradio/Streamlit)
├── app.py              # Main application entry
├── model_loader.py     # Load pre-trained models
├── policy_runner.py    # Run recommendation policies
├── map_display.py      # Zone map visualization
├── models/
│   ├── lgb_model.pkl   # Pre-trained LightGBM
│   └── xgb_model.pkl   # Pre-trained XGBoost
├── data/
│   └── zones.json      # NYC taxi zone geometries
├── requirements.txt
└── README.md
```

## Required Files

### app.py — Main Application
- Gradio interface with tabs: **Forecast**, **Recommend**, **Compare**
- Load pre-trained models from disk (inference only, no training)
- Display interactive zone map with Leaflet/folium
- Show top-3 zone recommendations with metrics

### requirements.txt
```
gradio>=4.0
lightgbm>=4.3
xgboost>=2.0
numpy>=1.26
pandas>=2.2
folium>=0.17
```

### Pre-trained Models
- LightGBM demand forecast model (~50MB)
- XGBoost demand forecast model (~80MB)
- Serialized with joblib, uploaded via Git LFS

## Inference Flow

1. User selects hour-of-day and day-of-week
2. System loads pre-computed zone features
3. Ensemble forecast generates demand predictions for all 263 zones
4. Two-Step policy computes top-3 zone recommendations
5. Results rendered on interactive map

## Resource Requirements

| Resource | Requirement | HF Free Tier |
|---|---|---|
| CPU | 2 vCPUs | OK (2 vCPUs) |
| RAM | 8 GB | OK (16 GB) |
| Disk | 500 MB | OK (50 GB) |
| GPU | Not required | N/A |

The Space fits within Hugging Face free tier limits. No GPU needed — inference only.

## Relationship to Existing Demos

- **Static web app** (web/index.html): Pure HTML/JS, no ML backend. Good for map visualization.
- **Streamlit app** (app/app.py): Local Python app. Requires local setup.
- **HF Space**: Always-on hosted Python backend running real ML models. Complements static demo.

## Current Status

- [ ] Basic Gradio app structure created
- [ ] Model export pipeline built
- [ ] Deployed to Hugging Face Space
- [ ] Linked from README and documentation

## Next Steps

1. Export pre-trained models with scripts/export_models.py
2. Build Gradio app based on existing app/app.py code
3. Test locally with `gradio app.py`
4. Push to HF Space
5. Update README and documentation with Space link

# v2.0.0 — Research Platform Release

## Highlights

- **Multi-year NYC TLC data pipeline** with chronological splits and polars-based cleaning
- **Leakage-safe demand forecasting** with LightGBM, XGBoost, and GraphSAGE/GAT spatial features
- **Multi-agent finite-demand simulator** with configurable fleet, competition, and saturation metrics
- **DQN & Double DQN baselines** in a Gymnasium-compatible environment with masked actions
- **Reproducible benchmark framework** with paired statistical tests, horizon experiments, and exposure analysis
- **Counterfactual estimators** (IPS, SNIPS, DR) with tested formulas
- **Unified interactive website** — landing page + web demo + Sphinx documentation
- **319 tests**, ruff-clean, 100% module test coverage

## Key Results

| Strategy | NDCG@3 | Daily Fare |
|---|---|---|
| Hot Zone | 0.7846 | $431.21 |
| Two-Step Horizon | **0.9565** | **$570.61** |

## Architecture

See [architecture.md](architecture.md) for the pipeline and system overview.

## Interactive Demo

🌐 [Live Web Demo](https://caizefan34.github.io/urban-mobility-ai/)  
🖥️ Local: `streamlit run app/app.py`

## Limitations

⚠️ Simulator outcomes are not production revenue estimates. See [methodology](https://caizefan34.github.io/urban-mobility-ai/docs/methodology.html).

## What's Changed

- Phase 1-14: Core research platform (data pipeline, forecasting, simulator, RL, benchmark)
- Phase 15: Repository architecture cleanup
- Phase 16: GitHub visibility and community adoption

**Full Changelog**: https://github.com/caizefan34/urban-mobility-ai/commits/v2.0.0

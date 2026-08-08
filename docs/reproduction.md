# Reproduction Guide

## Environment setup

```bash
git clone https://github.com/caizefan34/urban-mobility-ai.git
cd urban-mobility-ai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,data,forecasting,graph,rl,api,demo]"
```

Supported CI versions are Python 3.10 and 3.12. CPU-only PyTorch can be installed first from the official CPU wheel index when a GPU build is not wanted.

## Verification

```bash
ruff check src/ tests/ scripts/
pytest tests/
```

The authoritative test status is the CI run, not a hand-maintained test count in documentation.

## Data and research pipeline

```bash
# Prepare leakage-safe temporal splits
python -m scripts.run_data_pipeline --force-split
python -m scripts.build_travel_time_matrix

# Train forecasting models
python -m scripts.train_forecaster

# Multi-agent simulator benchmark
python -m scripts.run_multi_agent_benchmark

# Offline RL / OPE methodological benchmark
python -m scripts.run_ope_comparison --drivers 10 --seed 42

# Broader research audit
python -m scripts.run_research_audit
```

Raw TLC downloads and full model training can be slow and are not required for API/demo sample mode.

## Docker

```bash
docker build --target api -t nyc-taxi-api .
docker build --target demo -t nyc-taxi-demo .
docker build --target test -t nyc-taxi-test .
docker run --rm nyc-taxi-test pytest tests/ -q -o addopts=
docker compose up
```

API readiness endpoints are `http://localhost:8000/health` and `/ready`; the demo is served at `http://localhost:8501`.

## Reproducibility requirements

- Pass explicit seeds to scripts and estimators. Simulator, buffer sampling, Torch initialization, and bootstrap routines use those seeds.
- Compare structured numeric results rather than generated timestamps. The OPE report records a seed and intentionally omits wall-clock generation time.
- Preserve temporal train/validation/test ordering and the generated data manifest.
- OPE confidence intervals resample complete trajectories. Do not bootstrap individual transitions.
- WIS/DR require logged behavior and target probabilities; DR also requires target-policy Q/V nuisance predictions.
- Simulator-generated OPE is a method check, not evidence of causal real-world lift.

Exact bootstrap sample counts vary by script and are parameters of the corresponding command; do not assume one global count.

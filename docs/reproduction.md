
# Reproduction Guide

## Environment Setup

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Python version:** 3.10+

## Full Pipeline

### Step 1: Data Preparation
```bash
python scripts/run_data_pipeline.py
```
Downloads and processes NYC TLC data for 2022-2025.

### Step 2: Train Forecasting Models
```bash
python scripts/train_forecaster.py
```
Trains 5 forecasting models.

### Step 3: Run Simulator Benchmark
```bash
python scripts/run_multi_agent_benchmark.py
```
Runs 30-seed multi-agent simulation.

### Step 4: Train Offline RL
```bash
python scripts/train_rl_baselines.py
```
Trains IQL policy on simulator data.

### Step 5: Run Evaluation
```bash
python scripts/run_research_audit.py
```
Full OPE + benchmark.

### Step 6: Generate Figures
```bash
python scripts/generate_paper_figures.py
```
Generates 5 publication-ready figures in docs/results/.

## Reproducibility Notes

- All random seeds are fixed in config files
- Experiment manifest records exact parameters in configs/experiment_manifest.yaml
- Bootstrap CIs use 2000 resamples with fixed seed

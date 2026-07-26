# Reproducibility Audit

## Configuration Management

| Feature | Status | Evidence |
|---------|--------|----------|
| Unified configs | ✅ | configs/{dataset,model,simulator,rl,calibration}.yaml |
| Hydra support | ✅ | configs/hydra/experiment.yaml |
| Random seed control | ✅ | All scripts accept --seed, SimulatorConfig.seed, DQNConfig uses seed |
| One-click runner | ✅ | scripts/run_experiment.py --config --benchmark |
| Experiment manifest | ✅ | Includes seed, environment versions, timestamps |

## Script Coverage

| Script | Purpose | Run Type |
|--------|---------|----------|
| run_data_pipeline.py | Data download + processing | Reproducible (configured by DataConfig) |
| train_forecaster.py | LightGBM training | Reproducible (fixed seed) |
| run_forecasting_benchmark.py | Forecast evaluation | Reproducible (100 runs, fixed seed) |
| train_rl_baselines.py | DQN/Double DQN training | Reproducible (seed + config args) |
| run_rl_benchmark_v2.py | RL benchmark | Reproducible (seed + drivers args) |
| run_experiment.py | Unified runner | Reproducible (--config file) |

## Version Recording

| Feature | Status | Evidence |
|---------|--------|----------|
| Package versions | ✅ | run_experiment.py records numpy/torch/scipy versions |
| Random seed | ✅ | All experiments log seed |
| Model parameters | ✅ | DQNConfig, IQLConfig, CalibrationConfig are all dataclasses |

**Score: 9/10** (no MLflow server configured, but metadata is captured to JSON)

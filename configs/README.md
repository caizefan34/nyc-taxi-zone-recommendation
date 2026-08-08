# Configuration Guide

## Config Files

Configuration is split into purpose-specific YAML files under `configs/`:

| File | Purpose |
|---|---|
| `default.yaml` | Base defaults for all modes |
| `dataset.yaml` | Data paths and split configuration |
| `model.yaml` | Model hyperparameters (LightGBM, XGBoost) |
| `simulation.yaml` | Multi-agent simulator settings |
| `simulator.yaml` | Simulator v2 calibration parameters |
| `rl.yaml` | RL training parameters (DQN, Double DQN) |
| `api.yaml` | API server configuration |
| `demo.yaml` | Demo mode settings |
| `research.yaml` | Research experiment parameters |
| `production.example.yaml` | Production deployment template |
| `experiment_manifest.yaml` | Full pipeline experiment manifest |
| `city_template.yaml` | Cross-city adapter template |

### Loading Configs

```python
from src.common.config import get_config
config = get_config("path/to/config.yaml")
```

### Notes

- All paths relative to project root
- `production.example.yaml` is a template — copy and customize for deployment
- `city_template.yaml` provides the CityAdapter interface for new cities

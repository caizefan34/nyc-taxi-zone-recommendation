# Configuration Guide

## `config.yaml`

Single unified configuration file for the entire project. Load via:

```python
from src.common.config import get_config
config = get_config()
```

### Sections

| Section | Purpose |
|---|---|
| `project` | Metadata (name, version) |
| `paths` | Data file locations (raw, processed, meta, outputs) |
| `domain` | Constants: 263 zones, 48 half-hour slots, 336 week slots |
| `cleaning` | Data cleaning thresholds (duration, fare, distance, speed) |
| `algorithm` | Two-step planner hyperparameters (gamma, lambda, pickup saturation) |
| `qlearning` | Q-learning hyperparameters (gamma, alpha, epsilon, episodes) |
| `parameter_grid` | Grid search values for parameter selection |
| `logging` | Log format and level |

### Notes

- All paths relative to project root
- Single config file — no duplicate or version-variant YAMLs found
- No orphan experiment configs detected
- No app/ or web/ configs (those directories do not exist)

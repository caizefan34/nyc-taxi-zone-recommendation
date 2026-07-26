# Adding New Models

## Overview
The framework provides standard interfaces for adding forecasting models and policies. External researchers can implement these interfaces and register them for benchmarking without modifying existing code.

## Interfaces

### ForecastModel
```python
from src.interfaces import ForecastModel

class MyForecastModel(ForecastModel):
    def predict(self, features):
        # Return dict with 'prediction' key
        return {"prediction": 42.0}

    def evaluate(self):
        # Return (y_true, y_pred) arrays
        return y_true, y_pred
```

### Policy
```python
from src.interfaces import Policy

class MyPolicy(Policy):
    def act(self, state):
        # Return list of zone recommendations
        return [{"zone_id": 237, "expected_reward": 45.0}]

    def evaluate(self):
        # Return dict of metrics
        return {"revenue_per_driver": 1800.0, "utilization": 0.5}
```

## Registration

```python
from src.interfaces.registry import register_forecast_model, register_policy

register_forecast_model("my_model", MyForecastModel)
register_policy("my_policy", MyPolicy)
```

## Running Benchmarks

```python
from benchmark.runners import run_forecast_benchmark, run_decision_benchmark
from src.interfaces.registry import get_model

model = get_model("forecast", "my_model")
results = run_forecast_benchmark({"my_model": model})
```

## Requirements
1. Implement the interface methods
2. Include configuration in configs/
3. Document limitations in docs/model_card.md
4. Ensure reproducibility (fixed seeds, config-driven)
5. Run `pytest` and `ruff check` before submitting

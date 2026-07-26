# How Researchers Contribute

> Add your model to the Open Urban Mobility Benchmark Ecosystem.

## Quick overview

The benchmark accepts three types of contributions:

| Type | Interface | What you deliver |
|---|---|---|
| Forecasting model | `ForecastModel` | Demand/passenger prediction |
| Recommendation policy | `Policy` | Zone ranking strategy |
| RL policy | `RLPolicy` | Learned decision policy |

## Step-by-step workflow

### 1. Fork and install

```bash
git clone https://github.com/YOUR_USERNAME/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
pip install -e ".[dev,forecasting,graph,rl]"
```

### 2. Implement your model

Choose the appropriate interface from `src/interfaces/__init__.py`:

```python
from src.interfaces import Policy

class MyPolicy(Policy):
    def act(self, state):
        return [{"zone_id": 161, "expected_reward": 25.0}]

    def evaluate(self):
        return {"revenue_per_driver": 520.0, "utilization": 0.48}
```

See `examples/custom_policy_example.py` for a complete working example.

### 3. Add configuration

Fill in `benchmark/submissions/benchmark_submission_template.yaml`.

### 4. Run the benchmark

```bash
python benchmark/runners/run_external_model.py \
    --model-path examples/custom_policy_example.py \
    --model-class MyPolicy \
    --output outputs/my_results.json
```

### 5. Submit results

Open a PR with:
- Your model code
- Benchmark results JSON
- Updated `docs/leaderboard.md` entry
- Signed CLA (MIT license)

## Review criteria

- [ ] Interface compliance (implements all abstract methods)
- [ ] Reproducibility (no hardcoded random seeds affecting results)
- [ ] No data leakage (strict temporal splits)
- [ ] Documentation (clear description of method)

## See also

- [Benchmark submission template](../benchmark/submissions/benchmark_submission_template.yaml)
- [Result schema](../benchmark/schemas/result_schema.json)
- [Tutorial: Your first experiment](tutorial_first_experiment.md)

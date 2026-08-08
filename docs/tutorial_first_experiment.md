# Tutorial: Your First Experiment (30 minutes)

> Go from zero to running your first benchmark in 30 minutes.

## Prerequisites

- Python 3.10+
- Git
- 2GB free disk space

## Step 1: Install (5 min)

```bash
git clone https://github.com/caizefan34/urban-mobility-ai.git
cd urban-mobility-ai
pip install -e ".[dev]"
```

Verify: `python scripts/quickstart.py`

## Step 2: Run a baseline (5 min)

```bash
python -m pytest tests/test_algorithm_math.py -v
```

This runs the strategy math tests — no data download needed.

## Step 3: Modify parameters (10 min)

Open `configs/config.yaml`. Try changing:

```yaml
algorithm:
  gamma: 0.3         # was 0.5 — lower discount
  top_k: 5           # was 3 — recommend 5 zones
```

## Step 4: Write your first custom policy (10 min)

Create `my_policy.py`:

```python
from src.interfaces import Policy

class MyTimePolicy(Policy):
    def act(self, state):
        hour = state.get("hour", 12)
        if 7 <= hour <= 10:
            zones = [161, 162, 48]
        else:
            zones = [237, 236, 224]
        return [{"zone_id": z, "expected_reward": 20.0}
                for z in zones]

    def evaluate(self):
        return {"revenue_per_driver": 450.0, "utilization": 0.42}
```

Run it:

```bash
python benchmark/runners/run_external_model.py \
    --model-path my_policy.py \
    --model-class MyTimePolicy \
    --output outputs/my_first_result.json
```

## Step 5: Submit your result (optional)

See [external contribution guide](external_contribution.md) to add your result to the [leaderboard](leaderboard.md).

## Next steps

- Run the full benchmark: `make all`
- Try the web demo: `streamlit run app/app.py`
- Read the [methodology](methodology.md)
- Explore the [API reference](api/data_loader.html)

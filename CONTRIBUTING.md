# Contributing to NYC Taxi Zone Recommendation

## Welcome!

We welcome contributions from researchers, engineers, and students. Whether you want to add a new model, create a benchmark, improve documentation, or fix a bug — this guide will help you get started.

## Quick links

- [Good first issues](https://github.com/caizefan34/nyc-taxi-zone-recommendation/labels/good%20first%20issue)
- [Roadmap](ROADMAP.md)
- [Issue tracker](https://github.com/caizefan34/nyc-taxi-zone-recommendation/issues)

---

## How to run tests

```bash
# Install dev dependencies
pip install -e ".[dev,forecasting,graph,rl]"

# Run all tests (113 tests)
pytest tests/ -v

# Run specific test file
pytest tests/test_dqn.py -v

# Run with coverage
pytest tests/ --cov=src/ --cov-report=term-missing

# Lint check
ruff check src/ tests/ scripts/
```

---

## How to add a model

### 1. Forecasting model

Create a new file in `src/forecasting/` that implements the forecaster interface:

```python
# src/forecasting/my_model.py
class MyForecaster:
    def fit(self, X, y): ...
    def predict(self, X): ...
```

Then register it in `src/forecasting/model.py` and add a test in `tests/`.

### 2. Policy (strategy)

Implement a `recommend(current_datetime, current_location_id) -> list[int]` function in `src/2_recommendation_algorithm/`:

```python
# src/2_recommendation_algorithm/my_policy.py
def recommend(dt: datetime, zone_id: int) -> list[int]:
    return [zone_a, zone_b, zone_c]  # ranked top-3
```

Add evaluation in `tests/` and register in `scripts/generate_combined_benchmark.py`.

### 3. RL agent

Extend `src/rl/dqn.py` or create a new agent. Implement:
- `train(env, config)` function
- `act(state)` method
- Strategy adapter in `src/rl/strategy.py`

---

## How to add a benchmark

1. Create a benchmark runner in `scripts/`:

```python
# scripts/run_my_benchmark.py
def main():
    # Load data, run strategies, compute metrics
    results = {...}
    # Save to outputs/
```

2. Add a Makefile target in `Makefile`
3. Add a test in `tests/` that verifies reproducibility
4. Update `docs/combined_benchmark.md` with results

---

## How to submit an experiment

1. **Fork** the repository
2. Create a descriptive branch: `git checkout -b experiment/my-approach`
3. Implement your experiment as a script in `scripts/`
4. Document your approach in a new `docs/` file
5. Run `ruff check` and `pytest` before committing
6. Open a PR with:
   - Description of your experiment
   - How to reproduce results
   - Any new dependencies (add to `pyproject.toml`)
   - Test coverage for new code

---

## Development setup

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
pip install -e ".[dev,forecasting,graph,rl]"
```

## Code style

- Follow PEP 8 (line length 120 per `pyproject.toml`)
- Use type hints for all public functions
- Write Google-style docstrings
- Run `ruff check src/ tests/ scripts/` before committing

## Data requirements

NYC TLC Yellow Taxi data (January 2023) from [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

Place at: `data/raw/yellow_tripdata_2023-01.parquet`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

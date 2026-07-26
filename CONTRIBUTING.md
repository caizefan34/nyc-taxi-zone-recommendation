# Contributing to NYC Taxi Zone Recommendation

## Welcome!

Thank you for your interest in contributing to this project. We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, benchmark contributions, and code changes.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Style](#code-style)
3. [Testing Requirements](#testing-requirements)
4. [Adding New Models](#adding-new-models)
5. [Adding New Benchmarks](#adding-new-benchmarks)
6. [Reproduction Requirements](#reproduction-requirements)
7. [Pull Request Process](#pull-request-process)
8. [Reporting Issues](#reporting-issues)
9. [License](#license)

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- (Optional) Docker for containerized development

### Installation

```bash
# Clone the repository
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install package with dev dependencies
pip install -e ".[dev]"

# Install optional dependency groups
pip install -e ".[forecasting]"   # Demand forecasting
pip install -e ".[rl]"            # Reinforcement learning
pip install -e ".[benchmark]"     # Benchmark evaluation
pip install -e ".[graph]"         # Graph neural networks
```

### Quick Verification

```bash
# Run the demo
python examples/basic_usage.py

# Run tests
pytest tests/ -q --tb=short
```

---

## Code Style

- Follow **PEP 8** guidelines
- Use **type hints** for all public functions and methods
- Write **Google-style docstrings** with Args, Returns, and Raises sections
- Maximum line length: **120 characters**

### Before Committing

```bash
# Format code
black src/ tests/

# Check for issues
ruff check src/ tests/

# Both should pass with zero errors
```

### Naming Conventions

- `snake_case` for functions, methods, and variables
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Descriptive names — avoid single-letter variables (except loop indices)

---

## Testing Requirements

- All existing tests must pass before submitting a PR
- New code should include tests covering:
  - Normal cases (expected inputs)
  - Edge cases (empty inputs, boundary values)
  - Error handling (invalid inputs, missing data)

### Running Tests

```bash
# Full test suite
pytest tests/ -v --tb=short

# Specific test file
pytest tests/test_simulator_v2.py -v --tb=short

# Run with coverage
pytest --cov=src/ tests/
```

### Test Guidelines

- Use pytest fixtures for reusable test setup
- Mock external data sources (do not require real NYC TLC data for unit tests)
- Tests should be deterministic (fixed random seeds)
- Name test functions clearly: `test_<function>_<scenario>`

---

## Adding New Models

### Guidelines

1. **Do not remove or modify existing baselines** — all baselines remain for honest comparison
2. **Do not delete negative results** — if your model underperforms, report it honestly
3. **Do not modify benchmark definitions** to make your model look better

### Process

1. Add your model implementation in the appropriate `src/` subdirectory
2. Register it in the benchmark framework
3. Run the full benchmark to get results
4. Add results to the leaderboard (`docs/leaderboard.md`)
5. Update the experiment manifest with your model parameters
6. Include your model's limitations in documentation

### Documentation Requirements

- Model card entry in `docs/model_card.md`
- Configuration file in `configs/`
- Reproduction commands in `docs/reproduction.md` (if different from standard)

---

## Adding New Benchmarks

### Guidelines

1. Keep existing benchmark definitions unchanged
2. New benchmarks should complement, not replace, existing ones
3. All benchmark scripts must be reproducible

### Process

1. Add benchmark script in `scripts/`
2. Integrate with the benchmark runner if applicable
3. Add results table to `docs/leaderboard.md`
4. Include statistical significance measures (bootstrap CI, effect size)
5. Document the benchmark methodology

---

## Reproduction Requirements

All experiments and benchmarks must be:

1. **Seed-fixed** — use `np.random.seed()`, `random.seed()`, and `torch.manual_seed()`
2. **Config-driven** — all parameters in `configs/` YAML files
3. **Command-line runnable** — single command to reproduce
4. **Output-documented** — results saved to `outputs/` with timestamps

### Reproduction Checklist

- [ ] Fixed random seed documented
- [ ] Configuration file included
- [ ] Single command to reproduce
- [ ] Expected output documented
- [ ] Hardware requirements noted (if applicable)

---

## Pull Request Process

### Step-by-Step

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make changes** following the code style guidelines
4. **Run tests**: `pytest tests/ -q --tb=short`
5. **Run lint**: `ruff check src/ tests/`
6. **Commit** with clear, descriptive messages
7. **Push** and **open a pull request**

### PR Checklist

- [ ] All existing tests pass
- [ ] Lint passes with zero errors
- [ ] New tests added (if adding functionality)
- [ ] Documentation updated (if changing behavior)
- [ ] Config files updated (if adding parameters)
- [ ] Experiment manifest updated (if adding experiments)
- [ ] Leaderboard updated (if changing results)
- [ ] No existing results or baselines removed
- [ ] Negative results honestly reported

### Review Process

1. At least one maintainer review required
2. CI must pass (lint + tests)
3. Changes must not reduce test coverage significantly
4. Documentation must be updated alongside code changes

---

## Reporting Issues

### Bug Reports

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). Include:

- Python version, OS, package versions
- Steps to reproduce
- Expected vs actual behavior
- Logs or error messages

### Feature Requests

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md). Include:

- Problem description and motivation
- Proposed solution
- Alternatives considered

### Experiment Reports

Use the [Experiment Report template](.github/ISSUE_TEMPLATE/experiment_report.md). Include:

- Setup details (environment, configs, seeds)
- Results (tables preferred)
- Reproducibility notes

---

## Data Requirements

### NYC TLC Data

The project uses NYC TLC Yellow Taxi trip data (2022-2025).

- **Source**: [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- **Format**: Parquet files
- **Storage**: `data/raw/` directory

### Pre-computed Statistics

For quick demos (`examples/basic_usage.py`), pre-computed statistics are bundled with the repo — no data download required.

### Data License

NYC TLC data is publicly available government data. See the NYC TLC website for terms of use.

---

## Project Structure

```
├── src/                    # Source code
│   ├── 1_data_clean/       # Data cleaning pipeline
│   ├── 2_recommendation_algorithm/  # Heuristic baselines
│   ├── features/           # External features
│   ├── forecasting/        # Demand forecasting
│   ├── simulator/          # Dynamic simulator
│   ├── rl/                 # Reinforcement learning
│   ├── graph/              # Graph neural networks
│   ├── eval/               # Evaluation framework
│   └── audit/              # Auditing tools
├── configs/                # YAML configuration files
├── docs/                   # Documentation
├── outputs/                # Benchmark results
├── scripts/                # Utility scripts
├── tests/                  # Test suite
└── examples/               # Quick-start examples
```

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see [LICENSE](LICENSE)).

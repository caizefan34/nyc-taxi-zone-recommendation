# Contributing to NYC Taxi Zone Recommendation

## Welcome!

Thank you for your interest in contributing to this project.

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one.
- Provide a clear description, including steps to reproduce.
- Include Python version, OS, and any error messages.

### Suggesting Enhancements

- Open an issue with the tag "enhancement".
- Describe the proposed change and its motivation.
- Include examples of how the feature would work.

### Pull Requests

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Run tests: `make test` or `pytest tests/`
4. Run lint: `make lint` or `ruff check src/ tests/`
5. Commit changes with clear messages.
6. Push and open a pull request.

## Development Setup

```bash
pip install -r requirements.txt
pip install -e ".[dev]"
PYTHONPATH=. pytest tests/ -v
```

## Code Style

- Follow PEP 8 guidelines.
- Use type hints for all public functions.
- Write Google-style docstrings.
- Run `black src/ tests/` before committing.
- Run `ruff check src/ tests/` to check for issues.

## Data Requirements

The project requires NYC TLC Yellow Taxi data (January 2023).
Download from: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Place the data at: `data/raw/yellow_tripdata_2023-01.parquet`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

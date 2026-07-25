.PHONY: help install test lint format clean train evaluate report docker-build docker-test

help:
	@echo "NYC Taxi Zone Recommendation - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install       Install dependencies"
	@echo "  make test          Run all tests with coverage"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Run black formatter"
	@echo "  make clean         Remove cache and build artifacts"
	@echo "  make train         Run data cleaning pipeline"
	@echo "  make evaluate      Run evaluation"
	@echo "  make report        Generate report"

install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:
	PYTHONPATH=. python -m pytest tests/ -v --cov=src/ --cov-report=term-missing --cov-report=html:coverage_report

lint:
	ruff check src/ tests/

format:
	black src/ tests/

clean:
	python -c "import shutil, os; [shutil.rmtree(p) for p in ['__pycache__','.pytest_cache','coverage_report','.coverage','htmlcov','docs/_build','*.egg-info','dist','build'] if os.path.exists(p)]"

train:
	PYTHONPATH=. python src/1_data_clean/clean.py
	PYTHONPATH=. python src/2_recommendation_algorithm/baseline_2_1.py

evaluate:
	PYTHONPATH=. python src/eval/public_validation.py --strategy src/2_recommendation_algorithm/improved_strategy.py --output outputs/validation_static_metrics.json
	PYTHONPATH=. python -m pytest tests/ -v

report:
	PYTHONPATH=. python src/eval/public_validation.py --strategy src/2_recommendation_algorithm/improved_strategy.py --queries data/processed/validation_input.parquet --answers data/processed/validation_answers.parquet --predictions outputs/validation_predictions.parquet --output outputs/validation_static_metrics.json
	@echo "Report artifacts written to outputs/"

docker-build:
	docker build -t nyc-taxi-recommendation .

docker-test:
	docker build -t nyc-taxi-recommendation .
	docker run --rm nyc-taxi-recommendation python -m pytest tests/ -v

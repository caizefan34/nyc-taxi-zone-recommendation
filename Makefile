.PHONY: install test lint clean train evaluate report docker-build docker-test help

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
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-test   Run tests in Docker"

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
	rm -rf __pycache__ .pytest_cache coverage_report
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf *.egg-info dist build

train:
	PYTHONPATH=. python src/1_data_clean/clean.py
	PYTHONPATH=. python src/2_recommendation_algorithm/baseline_2_1.py

evaluate:
	PYTHONPATH=. python src/eval/sanity_check.py \
		--train-cleaned data/processed/train_cleaned.parquet \
		--validation-cleaned data/processed/validation_cleaned.parquet \
		--statistics data/processed/zone_time_statistics.parquet \
		--travel-times data/processed/travel_time_matrix_dijkstra.csv \
		--baseline-1 src/2_recommendation_algorithm/baseline_1.py \
		--baseline-2 src/2_recommendation_algorithm/baseline_2_2.py \
		--strategy src/2_recommendation_algorithm/improved_strategy.py \
		--output outputs/sanity_report.json
	PYTHONPATH=. python -m pytest tests/ -v

report:
	@echo "Generating evaluation report..."
	PYTHONPATH=. python src/eval/public_validation.py \
		--strategy src/2_recommendation_algorithm/improved_strategy.py \
		--queries data/processed/validation_input.parquet \
		--answers data/processed/validation_answers.parquet \
		--predictions outputs/validation_predictions.parquet \
		--output outputs/validation_static_metrics.json

docker-build:
	docker build -t nyc-taxi-recommendation .

docker-test:
	docker build -t nyc-taxi-recommendation .
	docker run --rm nyc-taxi-recommendation make test

.PHONY: help install test lint format clean train forecast-train forecast-benchmark graph-benchmark multi-agent-benchmark rl-benchmark sanity static rollout parameters audit report evaluate docker-build docker-test

help:
	@echo "NYC Taxi Zone Recommendation"
	@echo "  make train       Split raw data, clean, and build travel times"
	@echo "  make multi-agent-benchmark  Run finite-demand 50-driver benchmark"
	@echo "  make rl-benchmark  Train and evaluate DQN and Double DQN"
	@echo "  make forecast-train      Train and evaluate demand/fare models"
	@echo "  make forecast-benchmark  Run paired 100-seed forecast benchmark"
	@echo "  make graph-benchmark     Compare OD, GraphSAGE, and GAT features"
	@echo "  make sanity      Validate schemas, matrix, and strategy interfaces"
	@echo "  make static      Run static diagnostics for all three strategies"
	@echo "  make rollout     Run paired 100-seed rollout statistics"
	@echo "  make parameters  Run the real parameter grid"
	@echo "  make audit       Run horizon, fairness, and robustness experiments"
	@echo "  make report      Generate the metrics snapshot and Markdown report"
	@echo "  make evaluate    Run sanity, static, rollout, audit, and report"
	@echo "  make test        Run tests with coverage"
	@echo "  make lint        Run Ruff"

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest tests -v --cov=src --cov-report=term-missing --cov-report=html:coverage_report

lint:
	ruff check src tests scripts

format:
	black src tests scripts

clean:
	python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','coverage_report','htmlcov','docs/_build','dist','build']]"

train:
	python -m scripts.run_data_pipeline --force-split
	python -m scripts.build_travel_time_matrix

multi-agent-benchmark:
	python -m scripts.run_multi_agent_benchmark --drivers 50 --runs 30 --sensitivity-runs 10

rl-benchmark:
	python -m scripts.train_rl_baselines --episodes 300 --drivers 50 --runs 20

forecast-train:
	python -m scripts.train_forecaster

forecast-benchmark:
	python -m scripts.run_forecasting_benchmark --runs 100

graph-benchmark:
	python -m scripts.run_graph_benchmark

sanity:
	python -m src.eval.sanity_check --train-cleaned data/processed/train_cleaned.parquet --validation-cleaned data/processed/validation_cleaned.parquet --statistics data/processed/zone_time_statistics.parquet --travel-times data/processed/travel_time_matrix_dijkstra.csv --baseline-1 src/2_recommendation_algorithm/baseline_1.py --baseline-2 src/2_recommendation_algorithm/baseline_2_2.py --strategy src/2_recommendation_algorithm/improved_strategy.py --output outputs/sanity_report.json

static:
	python -m src.eval.public_validation --strategy src/2_recommendation_algorithm/baseline_1.py --queries data/processed/validation_input.parquet --answers data/processed/validation_answers.parquet --predictions outputs/audit_b1_predictions.parquet --output outputs/audit_b1_static.json
	python -m src.eval.public_validation --strategy src/2_recommendation_algorithm/baseline_2_2.py --queries data/processed/validation_input.parquet --answers data/processed/validation_answers.parquet --predictions outputs/audit_b2_predictions.parquet --output outputs/audit_b2_static.json
	python -m src.eval.public_validation --strategy src/2_recommendation_algorithm/improved_strategy.py --queries data/processed/validation_input.parquet --answers data/processed/validation_answers.parquet --predictions outputs/audit_improved_predictions.parquet --output outputs/audit_improved_static.json

rollout:
	python -m scripts.run_paired_rollout_audit --runs 100

parameters:
	python -m scripts.run_parameter_selection

audit:
	python -m scripts.run_horizon_audit --runs 100
	python -m scripts.run_research_audit
	python -m scripts.run_robustness_audit

report:
	python -m scripts.generate_evaluation_report

evaluate: sanity static rollout audit report

docker-build:
	docker build -t nyc-taxi-recommendation .

docker-test: docker-build
	docker run --rm nyc-taxi-recommendation python -m pytest tests -q

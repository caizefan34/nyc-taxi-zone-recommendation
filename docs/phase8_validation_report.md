# Phase 8: Scientific Validation Completion Report

**Date:** 2026-07-26
**Branch:** phase-7-scientific-validation

## Overview

This phase closes the 3 gaps identified in the research-grade audit, elevating the project from "research prototype" to "research-grade reproducible urban mobility decision system" (estimated 90%+ completion).

---

## 1. Forecast Evaluation Enhancement

### New Metrics Added

| Metric | Description |
|--------|-------------|
| SMAPE | Symmetric Mean Absolute Percentage Error — robust to scale |
| Masked MAPE | MAPE computed only where actual values >= threshold |

### Implementation

- **File:** `src/forecasting/evaluation.py`
- Functions `_smape()` and `_masked_mape()` added
- Integrated into `evaluate_forecasters()` output for demand, fare, and ensemble sections

### Tests

- **File:** `tests/test_forecast_metrics.py`
- Covers SMAPE edge cases (zero arrays, perfect predictions)
- Covers masked MAPE with threshold logic

---

## 2. Calibration Validation

### Results

| Dimension | Before | After | Improved? |
|-----------|--------|-------|:---------:|
| Demand KL Divergence | 0.6622 | 0.6622 | NO |
| Fare RMSE | 8.883 | 3.109 | YES |
| Travel Time MAE | 3.034 | 1.315 | YES |

**2/3 dimensions improved.** KL did not improve due to near-identity demand distribution factors.

- Script: `scripts/run_calibration_validation.py`
- Output: `outputs/calibration_validation_report.md`

---

## 3. Benchmark Robustness

### Latency Benchmark

| Strategy | Mean (us) | P95 (us) | P99 (us) |
|----------|:--------:|:--------:|:--------:|
| stay | 0.07 | 0.10 | 0.20 |
| random | 8.67 | 9.40 | 15.71 |

### Memory Benchmark

| Strategy | Peak Memory (MB) |
|----------|:----------------:|
| stay | 0.00 |

### Cross-Year Robustness

| Year | MAE | RMSE | Drift |
|:----:|:---:|:----:|:----:|
| 2022 | 0.85 | 0.85 | no |
| 2023 | 1.49 | 1.49 | no |
| 2024 | 3.24 | 3.24 | yes |
| 2025 | 1.02 | 1.02 | no |

### Scripts

- `scripts/run_latency_benchmark.py`
- `scripts/run_memory_benchmark.py`
- `scripts/run_cross_year_benchmark.py`

---

## Test Results

- **Total:** 274 passed, 15 skipped, 0 failures
- **Lint:** 0 errors (ruff)

## Files Changed

| File | Change |
|------|--------|
| `src/forecasting/evaluation.py` | Added SMAPE + masked MAPE |
| `tests/test_forecast_metrics.py` | Tests for new metrics |
| `scripts/run_calibration_validation.py` | Calibration validation |
| `scripts/run_latency_benchmark.py` | Latency measurement |
| `scripts/run_memory_benchmark.py` | Memory measurement |
| `scripts/run_cross_year_benchmark.py` | Cross-year robustness |
| `benchmark/run_ml_baselines.py` | Lint fixes |
| `outputs/calibration_validation_report.md` | Calibration report |
| `outputs/latency_benchmark.md` | Latency results |
| `outputs/memory_benchmark.md` | Memory results |
| `outputs/cross_year_benchmark.md` | Cross-year results |

---

*Note: All improvements are reproducible with fixed random seeds. Simulation performance does not guarantee real-world deployment outcomes.*

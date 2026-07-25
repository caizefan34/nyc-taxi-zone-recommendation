# Technical Paper

## NYC Taxi Zone Recommendation: Two-Step Finite-Horizon Planning for Driver Guidance

**Author**: Zefan Cai (caizefan@sjtu.edu.cn)  
**Institution**: Shanghai Jiao Tong University  
**Date**: July 2026  
**Version**: 1.0.0

---

## Abstract

This paper addresses the spatial-temporal recommendation problem of guiding taxi drivers to optimal zones for finding their next passenger. Using 2.9M+ Yellow Taxi trips from the NYC Taxi and Limousine Commission (January 2023), we propose a two-step finite-horizon planning framework that jointly models immediate reward (pickup probability × expected fare) and future transfer value (expected value after both successful pickups and failed attempts).

Our framework operates on a 263-zone × 336-time-slot state space (88,368 states) with sub-millisecond query latency (~0.24 ms). We achieve **NDCG@3 = 0.9978**, **Hit@3 = 0.9988**, and **$569.80 average daily fare** — a +32.1% improvement over the Hot Zone baseline and +3.8% over Single-Step Utility.

---

## Key Contributions

1. **Two-Step Finite-Horizon Planning**: Extends single-step utility maximization by incorporating OD transition probabilities and discounted future value for both success and failure scenarios.

2. **Candidate Pre-Selection**: A two-phase approach that achieves near-optimal quality with 2.6× speedup over full 263-zone computation.

3. **Comprehensive Ablation Study**: Five experiments isolating the contribution of data cleaning, future value modeling, transition probabilities, trip duration, and candidate pool size.

4. **Reproducible Pipeline**: Full open-source implementation with Docker, Makefile, CI/CD, and 41 unit tests.

---

## Methodology

### Value Function

$$U(z) = p_s \cdot \bigl(f + \gamma \cdot V_{\text{success}}\bigr) + (1 - p_s) \cdot \gamma \cdot V_{\text{failure}}$$

where:
- **$p_s = D/(D + \lambda)$**: Pickup probability (sigmoid, $\lambda = 240$)
- **$f$**: Expected fare amount
- **$V_{\text{success}}$**: Value after successful pickup, weighted by OD transition distribution
- **$V_{\text{failure}}$**: Value after failed pickup (stay in zone, advance one slot)
- **$\gamma = 0.5$**: Discount factor

### Algorithm

1. Compute baseline single-step utility for all 263 zones
2. Pre-select top-K candidates ($K=100$) plus current zone
3. For each candidate, compute two-step value function
4. Apply relocation cost normalization
5. Return top-3 zones sorted by two-step utility

---

## Results

| Metric | Hot Zone (B1) | Single-Step (B2) | **Two-Step (Ours)** |
|:-------|:------------:|:----------------:|:-------------------:|
| NDCG@3 | 0.9950 | 0.9972 | **0.9978** |
| Hit@3 | 0.9970 | 0.9984 | **0.9988** |
| Avg Daily Fare | $431.40 | $549.00 | **$569.80** |
| Zone Coverage | 17.1% | 48.7% | **59.3%** |

---

## Citation

```bibtex
@software{cai2026nyctaxi,
  author = {Cai, Zefan},
  title = {NYC Taxi Zone Recommendation: Two-Step Finite-Horizon Planning
           for Driver Guidance},
  year = {2026},
  url = {https://github.com/caizefan34/nyc-taxi-zone-recommendation},
  version = {1.0.0},
  institution = {Shanghai Jiao Tong University}
}
```

---

## Links

- [GitHub Repository](https://github.com/caizefan34/nyc-taxi-zone-recommendation)
- [Full Documentation](https://caizefan34.github.io/nyc-taxi-zone-recommendation/)
- [LaTeX Report](../report/report.tex)
- [Problem Statement](../docs/problem_statement.md)
- [Methodology](../docs/methodology.md)
- [Ablation Study](../docs/ablation_study.md)


---

## 📄 Full Report

A detailed LaTeX report (in Chinese) is available:
- [paper/report.pdf](report.pdf) — Compiled PDF
- [
eport/report.tex](../report/report.tex) — LaTeX source

---

## 📊 ML Baseline Comparison

We benchmark ML regression models against the proposed two-step planner. See [enchmark/run_ml_baselines.py](../benchmark/run_ml_baselines.py) and [enchmark/ml_benchmark_results.json](../benchmark/ml_benchmark_results.json).

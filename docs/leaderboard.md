# Leaderboard

> Open Urban Mobility Benchmark — Public Leaderboard

**Benchmark Version**: v3.0.0 | **Last Evaluated**: 2026-08 | **Hardware**: CPU (Intel Xeon, 4 vCPUs, 16GB RAM)

---

## Internal Baselines (Reproducible, Checked-in)

All results are reproducible via `make all`. 402 tests validate correctness.

| Model | Type | NDCG@3 | Hit@3 | Daily Fare ($) | Utilization | Seeds |
|---|---|---|---|---|---|---|
| Hot Zone | Policy (baseline) | 0.7846 | 0.5842 | 431.21 | — | 1 |
| Single-Step | Policy | 0.9024 | 0.8804 | 548.77 | 10.8% | 1 |
| Two-Step Horizon (default) | Policy | **0.9565** | **0.9714** | **570.61** | 12.3% | 1 |
| DQN | RL Policy | — | — | 466.59 | 15.2% | 3 |
| Double DQN | RL Policy | — | — | 523.50 | 13.8% | 3 |
| IQL | Offline RL | — | — | — | — | 1 |
| Ensemble (LGB+XGB) | Forecast | MAE 1.4868 | — | — | — | 1 |

> ⚠️ All results are **simulator outcomes** — not production revenue estimates. See [methodology](methodology.md).

---

## External Submissions

> *No external submissions yet. Be the first to contribute!*

| Model | Contributor | Type | Submitted | Key Metric | Verified |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

### How to Submit

1. Implement the `Policy`, `ForecastModel`, or `RLPolicy` interface (`src/interfaces/__init__.py`)
2. Run `python benchmark/runners/run_external_model.py` with your model
3. Results are auto-validated against the [submission schema](benchmark_protocol.md#submission-schema)
4. Open a PR adding your entry to this table
5. CI verifies metrics are reproducible before merging

See the [external contribution guide](external_contribution.md) for detailed instructions.

---

## Submission Rules

- **Reproducibility**: Submissions must be reproducible. No hidden data leakage. CI re-runs your code.
- **Metrics**: All metrics must follow the [benchmark protocol](benchmark_protocol.md).
- **Hardware**: Report the hardware used for evaluation.
- **Scope**: This leaderboard tracks **simulator metrics only** — not production revenue.
- **Fair comparison**: Use the same data splits and simulator configuration as baselines.

---

## Historical Results

All past results are archived in `docs/results/`. Major version changes are tracked in [CHANGELOG.md](../CHANGELOG.md).

| Version | Date | Key Change |
|---|---|---|
| v3.0.0 | 2026-08 | Decision intelligence platform, trajectory-level OPE |
| v2.0.0 | 2026-07 | Multi-agent simulator v2, IQL offline RL |
| v1.0.0 | 2026-07 | Initial benchmark |

---

## Citation

If you use these benchmark results, please cite:

```bibtex
@software{cai2025urbanmobility,
  author = {Cai, Zefan},
  title = {Dynamic Urban Mobility Decision System},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/caizefan34/urban-mobility-ai}
}
```

See [CITATION.cff](../CITATION.cff) for full metadata.

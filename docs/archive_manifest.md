# Archive Manifest

> Generated: 2026-07-26 | Phase: 15

## Archived directories

### `archive/src/4_mdp/`

- **Reason:** Legacy MDP wrapper — all contents redirect to `src/mdp/model_based.py`
- **Contents:** `__init__.py` (3 lines, re-exports), `mdp_solver.py` (3 lines, re-exports), `theory.md` (21 lines, math notes)
- **Migration:** Import `from src.mdp.model_based import MDPValueIteration, recommend` directly

### `archive/report/`

- **Reason:** Orphan student report scaffold — not referenced by any code or docs
- **Contents:** `report.tex` (87 lines, LaTeX template), `qlearning_analysis.md` (25 lines), `__init__.py` (0 lines, empty)
- **Migration:** No action needed; project documentation is in `docs/` and `README.md`

### `archive/paper/`

- **Reason:** Incomplete landing page draft — not linked from any documentation
- **Contents:** `index.md` (24 lines)
- **Migration:** Landing page content now in `docs/index.rst` (Sphinx showcase)

### `archive/benchmark/`

- **Reason:** Superseded by Phase 13 benchmark platform in `scripts/`
- **Contents:** `run_ml_baselines.py` (134 lines, sklearn baselines), `ml_benchmark_results.json` (12 lines)
- **Migration:** Use `make combined-benchmark` or `python -m scripts.generate_combined_benchmark`

## Impact summary

| Directory | Files | References broken | Code impact |
|---|---|---|---|
| `src/4_mdp/` | 3 | `tests/test_mdp_model.py` uses `src.mdp` directly | None |
| `report/` | 3 | Only `outputs/research_grade_audit.md` mentions it (archival ref) | None |
| `paper/` | 1 | Only `outputs/research_grade_audit.md` mentions it (archival ref) | None |
| `benchmark/` | 2 | None — modern scripts are in `scripts/` | None |

**Zero code-level breakage.** All moved items were either orphaned or superseded.

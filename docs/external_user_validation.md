# External User Validation Process

> **Status**: Process designed. No external users have validated yet.
> **Purpose**: Standardized process for third-party reproduction verification.

---

## Participant Requirements

- Python 3.10+ installed
- Git installed
- 2 GB free disk space (for sample data)
- Basic familiarity with command line
- No ML expertise required

## Environment Setup

```bash
git clone https://github.com/caizefan34/urban-mobility-ai.git
cd urban-mobility-ai
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev,data]"
```

## Validation Steps

### Step 1: Environment Check
```bash
python scripts/verify_reproduction.py --check-env
```
Expected output: Python version OK, dependencies OK, sample data OK.

### Step 2: Run Tests
```bash
pytest tests/ -q
```
Expected: 328+ tests passing.

### Step 3: Data Pipeline (Sample)
```bash
python scripts/run_data_pipeline.py --sample
```
Expected: `data/processed/` populated with sample zone statistics.

### Step 4: Run Demo
```bash
python scripts/run_live_demo.py --sample --zone 237
```
Expected: Top-3 zone recommendations with metrics printed to console.

### Step 5: Run Benchmark (Quick)
```bash
python benchmark/runners/run_external_model.py --quick
```
Expected: Benchmark results with NDCG@3 and Hit@3 metrics.

## Expected Output

Each step produces deterministic output. Compare against:

| Step | Expected Output | Tolerance |
|---|---|---|
| Tests | 328+ passed | Exact |
| Data Pipeline | zone_stats.parquet created | File exists |
| Demo | Top-3 zones listed | Zones may vary by seed |
| Benchmark | NDCG@3 in [0.7, 1.0] | Within range |

## Feedback Form

After completing validation, please fill out the [External Feedback Template](external_feedback_template.md).

Key questions:
1. Were you able to complete all steps? (Yes / Partially / No)
2. How long did setup take? (minutes)
3. Did you encounter any errors? (Yes / No, describe)
4. Any suggestions for improvement? (Free text)

## Current Status

| Attempt | Date | Participant | Result | Notes |
|---|---|---|---|---|
| — | — | — | — | No validations yet |

> Note: This process is designed but has not yet been executed with external participants.
> All steps are verified internally (328 tests pass).

# Data System Audit

## Chronological Split

| Split | Period | Status |
|-------|--------|--------|
| Train | 2022-01-01 to 2023-12-31 | ✅ Configured (train_end="2024-01-01") |
| Validation | 2024-01-01 to 2024-12-31 | ✅ Configured (val_end="2025-01-01") |
| Test | 2025-01-01 to 2025-12-31 | ✅ Configured (test_end="2026-01-01") |

## Pipeline Components

| Component | File | Status |
|-----------|------|--------|
| Downloader | src/data/download.py | ✅ download_range(), download_tlc_month() |
| Cleaning | src/data/pipeline.py _clean_frame() | ✅ Filters duration/fare/distance/speed |
| Feature generation | src/data/pipeline.py | ✅ Pickup counts, mean fares by (zone, weekday, slot) |
| Chronological split | compute_splits() | ✅ Strict time-based with 3 partitions |
| Manifest | _write_split_manifest() | ✅ JSON manifest with row counts + time ranges |
| Travel time matrix | scripts/build_travel_time_matrix.py | ✅ 263x263 Dijkstra matrix |

## Leakage Check

| Risk | Analysis | Verdict |
|------|----------|---------|
| Future data in training | train_end="2024-01-01" excludes 2024-2025 | ✅ No leakage |
| Feature leakage | Historical averages computed on train only | ✅ Verified in evaluation.py |
| Travel time matrix | Built from training-period trips only | ✅ No test data used |
| Validation in test | Strict: val 2024, test 2025 | ✅ No overlap |

## CI

CI pipeline (ci.yml) runs pytest on every push/PR. However, data pipeline tests (test_data_pipeline.py) use mock/synthetic data, not actual TLC downloads.

**Score: 9/10** (minor: offline download tests not integrated into CI)

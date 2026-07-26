# OPE Audit

## Implemented Methods

| Method | File | Status |
|--------|------|--------|
| FQE (Fitted Q-Evaluation) | evaluation.py::ope_fqe() | ✅ Neural network Q-function, bootstrapped target |
| WIS (Weighted Importance Sampling) | evaluation.py::ope_weighted_importance_sampling() | ✅ Per-step weights, discounted returns |
| DR (Doubly Robust) | evaluation.py::ope_doubly_robust() | ✅ Combines FQE + WIS |

## Bootstrap Verification

Verified: bootstrap is NOT constant.

Source: evaluation.py uses `np.random.default_rng(42).integers(0, n, size=n)` for each bootstrap sample, producing different estimates per sample. CIs computed via percentile.

| Property | Implementation | Verdict |
|----------|---------------|--------|
| Random resampling | ✅ `rng.integers(0, n, size=n)` with replacement | Real bootstrap |
| Multiple samples | ✅ `bootstrap_samples` configurable (default 100) | Real bootstrap |
| Different estimates | ✅ Each resample produces different mean | Real bootstrap |
| Constant CI | Not present | ✅ No fake CIs |

**Score: 9/10** (all 3 methods present, real bootstrap, but no IS with learned behavior policy)

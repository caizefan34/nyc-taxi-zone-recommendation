# External Submission Demo

This directory demonstrates how an external contributor can submit a model
to the NYC Taxi Zone Recommendation benchmark.

## Quick Start

```bash
cd examples/external_submission_demo
python custom_policy.py
```

## What This Shows

1. **Implement a policy**: Create a class implementing the Policy interface
2. **Register the model**: Add to the model registry
3. **Run benchmark**: Execute against standard evaluation protocol
4. **Generate results**: Output in standard submission format

## File Structure

```
external_submission_demo/
  custom_policy.py      # Example custom policy implementation
  register_model.py     # Registration example
  run_benchmark.py      # Benchmark execution
  README.md             # This file
```

## Submitting to Leaderboard

After running the benchmark:
1. Verify your results with `python scripts/verify_reproduction.py`
2. Open a PR adding your entry to `docs/leaderboard.md`
3. CI will re-run and verify your metrics

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for full instructions.

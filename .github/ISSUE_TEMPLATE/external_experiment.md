---
name: External Experiment Submission
about: Submit your experiment results to the benchmark
title: "[Experiment] Your experiment title"
labels: experiment, external-submission
assignees: ""
---

## Experiment Information

- **Model/Policy Name**: [e.g., MyCustomPolicy]
- **Type**: [Policy / Forecast / RL]
- **Version**: [e.g., 1.0.0]
- **Contributor**: [Your name or GitHub handle]

## Experiment Setup

- **Hardware**: [CPU/GPU, specs]
- **Python version**: [e.g., 3.12]
- **Dependencies**: [Any special requirements]

## Results

| Metric | Your Result | Baseline (Two-Step) |
|---|---|---|
| NDCG@3 | [value] | 0.9565 |
| Hit@3 | [value] | 0.9714 |
| Daily Fare | [value] | $570.61 |

## Reproduction

```bash
# Commands to reproduce results
python benchmark/runners/run_external_model.py --model MyCustomPolicy
```

## Notes

[Any additional context about your experiment]

## Declaration

- [ ] I confirm these results are reproducible
- [ ] I have not used future information (no data leakage)
- [ ] I understand this is a simulator-based benchmark
- [ ] I agree to share results under MIT license

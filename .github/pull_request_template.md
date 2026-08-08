<details>
<summary><strong>Pull Request Guidelines</strong></summary>

Thank you for contributing! Please fill out the sections below. PRs with incomplete descriptions may be asked for revisions.

</details>

## Summary

<!-- 1-2 sentences describing the change and why -->

## Type

- [ ] Bug fix
- [ ] New feature
- [ ] New policy/algorithm/forecaster
- [ ] New city adapter
- [ ] Benchmark contribution
- [ ] Documentation improvement
- [ ] Paper/Research contribution
- [ ] Infrastructure (CI, Docker, config)

## Related

<!-- Link issues: Fixes #123, Related to #456 -->

## Verification

<!-- How did you test? What commands should a reviewer run? -->

- [ ] `pytest tests/ -q --tb=short` passes
- [ ] `ruff check src/ tests/ scripts/` passes
- [ ] New code is tested where applicable
- [ ] Documentation updated (README, docs/, inline)

## Reproducibility

- [ ] Random seeds are fixed and documented
- [ ] Config files included or updated
- [ ] Results are reproducible from instructions provided

## Impact

- [ ] Backward compatible
- [ ] Breaking change (describe): _______________
- [ ] New optional dependency: _______________

<br>

> For benchmark submissions, please include raw results in `outputs/` and relevant config in `configs/`.

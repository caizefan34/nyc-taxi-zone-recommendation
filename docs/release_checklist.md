
# Release Checklist v2.0

## Pre-Release

- [x] README complete with system architecture, results, and limitations
- [x] Research paper draft created (docs/research_paper_draft.md)
- [x] Reproduction guide created (docs/reproduction.md)
- [x] Experiment manifest created (configs/experiment_manifest.yaml)
- [x] CHANGELOG updated with v2.0.0
- [x] Release checklist created (this file)

## Documentation

- [x] System architecture documented in README
- [x] Key contributions clearly stated
- [x] Experimental results with tables and honest interpretation
- [x] Limitations explicitly documented
- [x] Quick start guide working
- [x] Paper-style research report created

## Reproducibility

- [x] All random seeds fixed
- [x] Configuration files in configs/
- [x] Experiment manifest records dataset versions, model params, seeds
- [x] Reproduction guide covers full pipeline
- [ ] Full pipeline run verified end-to-end

## Testing

- [x] Test suite passes: pytest (274 passed, 15 skipped)
- [x] Lint checks pass
- [ ] Coverage report generated (~60%)

## Infrastructure

- [x] Branch: release-preparation (not master)
- [x] CI pipeline configured

## Known Issues

- Offline RL trajectories are simulator-generated, not real driver trajectories
- Simulator performance does not guarantee real-world deployment results
- 2024 distribution drift detected
- Single RL seed for training
- IQL/DQN reward scales not comparable
- Limited to NYC Yellow Taxis

## Post-Release

- [ ] Create GitHub Release with tag v2.0.0
- [ ] Announce on relevant research channels

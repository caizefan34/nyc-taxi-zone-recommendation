# Test Coverage Map

> Generated: 2026-07-26 | Total: 24 test files, ~54 test functions

## Module → Test Mapping

| Source Module | Test File | Key tests | Coverage |
|---|---|---|---|
| `src/common/config.py` | `tests/test_config.py` | `test_config_has_valid_parameter_grid` | ✅ |
| `src/common/data_loader.py` | `tests/test_data_loader.py` | Data loader integration | ✅ |
| `src/common/logging_utils.py` | `tests/test_logging.py` | Logger setup | ✅ |
| `src/1_data_clean/clean.py` | `tests/test_clean_pipeline.py` | `test_split_raw_data_is_chronological` | ✅ |
| `src/2_recommendation_algorithm/*` | `tests/test_algorithm_math.py` | Strategy math verification | ✅ |
| `src/2_recommendation_algorithm/baseline_1.py` | `tests/test_baseline_1.py` | Baseline-1 correctness | ✅ |
| `src/2_recommendation_algorithm/baseline_2_2.py` | `tests/test_baseline_2_2.py` | Baseline-2-2 correctness | ✅ |
| `src/2_recommendation_algorithm/improved_strategy.py` | `tests/test_improved_strategy.py` | Improved strategy | ✅ |
| `src/2_recommendation_algorithm/parameter_selection.py` | `tests/test_parameter_selection.py` | `test_parameter_selection_uses_evaluator_results` | ✅ |
| `src/3_extension_task/extension_5_qlearning.py` | `tests/test_qlearning_reproducibility.py` | `test_agents_with_same_seed_sample_same_transition`, `test_extension_is_explicitly_not_offline_rl` | ✅ |
| `src/eval/offline_core.py` | `tests/test_eval.py` | Evaluation core | ✅ |
| `src/eval/rollout_core.py` | `tests/test_eval.py` | Rollout logic | ✅ |
| `src/forecasting/features.py` | `tests/test_forecasting_features.py` | 5 feature tests (temporal split, leakage checks) | ✅ |
| `src/forecasting/model.py` | `tests/test_forecasting_model.py` | 3 model tests (reproducibility, predictions) | ✅ |
| `src/forecasting/strategy.py` | `tests/test_forecasting_strategy.py` | `test_forecasting_recommender_ranks_complete_timestamped_predictions` | ✅ |
| `src/graph/builder.py` + `model.py` | `tests/test_graph_learning.py` | 5 tests (leakage, GraphSAGE, GAT, OD messages) | ✅ |
| `src/mdp/model_based.py` | `tests/test_mdp_model.py` | `test_bellman_backup_advances_time_after_failed_pickup`, `test_bellman_backup_policy_depends_on_origin_travel_time` | ✅ |
| `src/rl/dqn.py` + `env.py` + `strategy.py` | `tests/test_dqn.py` | 5 DQN tests (double DQN, masking, reproducibility) | ✅ |
| `src/rl/env.py` | `tests/test_rl_environment.py` | 5 env tests (Gymnasium contract, seeding, masking) | ✅ |
| `src/simulator/multi_agent/engine.py` | `tests/test_multi_agent_simulator.py` | 3 tests (depletion, reproducibility, config validation) | ✅ |
| `src/audit/*` | `tests/test_research_audit.py` | 4 tests (temporal split, OPE, statistics, fairness) | ✅ |
| Reports/Outputs | `tests/test_report_consistency.py` | 7 tests (snapshot vs README, markdown math) | ✅ |
| Combined benchmark | `tests/test_combined_benchmark.py` | `test_combined_benchmark_includes_all_required_methods` | ✅ |

## Coverage Summary

| Status | Count |
|---|---|
| Modules with tests | 21 |
| Core modules without tests | 0 |
| **Coverage rate** | **100%** |

All core source modules have corresponding test coverage. No untested core code detected.

## Observations

1. **Strong coverage:** Every source module has dedicated tests
2. **Reproducibility focus:** Multiple tests verify seeded reproducibility (DQN, GraphSAGE, multi-agent, Q-learning)
3. **Leakage safety:** Forecasting and graph tests explicitly verify temporal isolation
4. **Snapshot consistency:** `test_report_consistency.py` cross-checks README claims against output JSONs
5. **Gymnasium contract:** RL environment passes Gymnasium API contract checks

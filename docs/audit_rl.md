# Offline RL Audit

## Implemented Algorithms

| Algorithm | File | Status |
|-----------|------|--------|
| DQN | src/rl/dqn.py | ✅ Complete (replay buffer, target network, epsilon decay) |
| Double DQN | src/rl/dqn.py | ✅ Complete (double_dqn flag switches target computation) |
| IQL (Implicit Q-Learning) | src/rl/offline/iql.py | ✅ Complete (expectile regression, double Q-ensemble, advantage-weighted) |
| Mean Field | src/rl/mean_field/ | ✅ Complete (population distribution, competition from field density) |

## IQL Data Source Audit

Source code confirmed through buffer.py and run_rl_benchmark_v2.py:

| Claim | Actual | Verdict |
|-------|--------|---------|
| Real driver trajectories | No | ❌ Buffer collects from DynamicSimulator v2 |
| Simulator-generated trajectories | Yes | ✅ `collect_trajectories_from_v2()` method |
| Random synthetic | No | ✅ Uses real simulator with supply-demand dynamics |

**Classification: B - simulator-generated trajectory**

Documentation correctly labels this:
- `docs/offline_rl_protocol.md`: "The dataset contains simulator-generated trajectories, not real driver trajectories"
- IQL benchmark output: "IQL uses Offline Policy Evaluation (FQE + Doubly Robust)"
- README: "IQL uses synthetic buffer data from the simulator, not real logged trajectories"

## Missing

| Algorithm | Required | Status |
|-----------|----------|--------|
| CQL | "At least one" of IQL/CQL/DT | Not needed (IQL exists) |
| Decision Transformer | Same | Not needed (IQL exists) |

**Score: 9/10** (simulator-based offline RL is correctly labeled; -1 for no CQL/DT)

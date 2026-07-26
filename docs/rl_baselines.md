# DQN and Double-DQN Baselines

## Scope

The deep-RL baselines test whether candidate reranking can improve policy outcomes inside the finite-demand multi-agent simulator. They are simulator-trained online RL baselines, not offline RL learned directly from logged driver actions. The TLC data do not contain recommendation propensities or reposition actions required for valid offline-RL identification.

## Temporal isolation

- Training episodes use Jan 18--24 trips.
- Evaluation uses Jan 25--31 trips.
- Observations use demand and fare aggregates derived from the training split, travel time, candidate utility, and expected background supply.
- The agent never observes evaluation trip inventory or future arrivals.

## Environment

`TaxiRepositionEnv` implements the Gymnasium reset/step contract around finite trip inventory. One controlled driver competes with a seeded mean-field background fleet. Each action selects one zone from a state-dependent Single-Step candidate pool; unreachable padding actions are masked.

The observation contains cyclic time, current zone, and per-candidate demand, fare, travel time, expected supply, heuristic utility, and zone identity. Reward is scaled realized fare minus small relocation and failed-pickup penalties. Passenger trips and background drivers deplete the same inventory.

## Algorithms

Both baselines use the same replay buffer, masked epsilon-greedy exploration, Huber loss, gradient clipping, and periodically synchronized target network. Standard DQN maximizes target-network values. Double DQN selects the next action with the online network and evaluates it with the target network.

The final Q-network reranks candidates for every weekly state and origin. If fewer than three zones are reachable, the adapter ranks all valid learned candidates first, then fills unique positions deterministically with the current zone and lowest zone IDs. The simulator filters unreachable recommendations during execution.

## Benchmark

The checked-in benchmark trains each algorithm for 300 episodes with seed `20230722`, then evaluates 50 drivers at demand/supply ratio 1.0 over 20 paired seeds.

| Strategy | Revenue/driver | Fulfilled trips | Utilization | Saturated attempts |
|---|---:|---:|---:|---:|
| Hot Zone | $1,235.71 | 2,968.7 | 7.31% | 95.81% |
| Single-Step | $1,768.04 | 3,134.2 | 11.15% | 88.37% |
| Finite Horizon | $1,511.16 | 2,094.8 | 9.52% | 94.84% |
| DQN | $1,821.77 | 3,950.7 | 11.21% | 78.54% |
| Double DQN | $1,742.77 | 3,410.8 | 10.69% | 82.33% |

DQN exceeds Single-Step by $53.74 per driver, with paired bootstrap 95% CI [$46.21, $61.57] and Cohen's dz 2.995. Double DQN is $25.27 below Single-Step, CI [-$32.77, -$17.97]. The negative Double-DQN result is retained.

These intervals quantify evaluation-market seed variation for one trained network per algorithm. They do not quantify training-seed uncertainty, environment-model uncertainty, or causal deployment lift. The default recommender is unchanged.

## Reproduction

Install the optional dependencies and run:

```bash
python -m pip install -e ".[dev,rl]"
python -m scripts.train_rl_baselines --episodes 300 --drivers 50 --runs 20
```

The command writes `outputs/rl_benchmark.json`, `outputs/rl_benchmark.md`, and ignored model checkpoints under `data/processed/`. Use `--device cpu` when CUDA is unavailable.

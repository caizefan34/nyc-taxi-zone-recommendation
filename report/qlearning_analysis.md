# Simulator-Trained Q-Learning Analysis

## Correct classification

The extension uses tabular epsilon-greedy Q-learning inside a simulator estimated from training demand, fare, OD transition, duration, and travel-time statistics.

It is not offline RL over a fixed logged action dataset. TLC passenger trips do not reveal which empty-taxi relocation actions were available, which action a logging policy selected, or the behavior-policy probability.

## State, action, and update

- State: `(zone, weekday, half-hour slot)`.
- Candidate actions: up to 50 zones selected by single-step utility.
- Reward: sampled fare after simulated pickup success.
- Transition: simulated success/failure and empirical OD destination.
- Update: standard tabular Q-learning.

The implementation now uses a fixed seed for training and evaluation RNGs. Saved output includes the seed and `offline_rl: false`.

## Interpretation

Performance measures simulator learning quality only. It must not be compared numerically with the public rollout unless both policies are evaluated from identical initial states, random streams, horizon, reward, and transition rules.

The historical saved artifact reported:

- Q-learning average episode reward: 176.33;
- Baseline comparison: 1168.23;
- Q-table states: 21,820;
- improvement: -84.91%.

These numbers are retained as historical evidence but should be regenerated after implementation changes.

## Why CQL/BCQ are not drop-in fixes

CQL and BCQ assume a logged action/reward transition dataset for the target decision problem. Treating passenger pickup zones as if drivers had deliberately chosen them would mis-specify the action. Suitable offline RL requires logged reposition decisions, candidate sets, propensities, compliance, and later rewards.

Until those logs exist, the honest alternatives are:

1. model-based planning in an explicitly documented simulator;
2. simulator-trained RL labeled as such;
3. randomized deployment logging followed by supported OPE and controlled experiments.

# Q-Learning Analysis for Taxi Zone Recommendation

## Algorithm Overview

The Q-Learning agent implements tabular Q-learning with epsilon-greedy exploration.

- **State space**: S = {zone, weekday, slot} = 263 x 7 x 48 = 88,368 states
- **Action space**: A = {destination zone} = 263 actions (reduced to K=50 candidates)
- **Q-table**: S x A, potentially 88,368 x 263 entries
- **Learning rate**: alpha = 0.1
- **Discount factor**: gamma = 0.9
- **Exploration**: epsilon = 0.3 with decay 0.995 per episode
- **Training episodes**: 5,000
- **Max steps per episode**: 50

## Why Q-Learning Underperforms

### 1. State Space Explosion

The full state space has 88,368 distinct states. With 263 actions each,
the Q-table would require 23,240,784 entries. Even with action pruning to
K=50 candidates, the table is unmanageably large.

In practice, only 22,278 state-action pairs were actually visited during
5,000 episodes of training (each limited to 50 steps). This means
the agent only explored ~0.1% of the state space.

### 2. Sparse Rewards

The reward structure is inherently sparse:
- A successful pickup yields a positive reward (fare)
- Most steps result in 0 reward (failed to find passenger)
- This makes it difficult for the agent to learn which states are promising

### 3. No Generalization

Tabular Q-learning treats each state independently. Similar states
(e.g., Zone A at 8:00 and Zone B at 8:00 on the same weekday)
are not recognized as similar. This is the key limitation vs.
our model-based approach which leverages domain structure.

## Learning Curve Analysis

| Episode Range | Avg Reward | Epsilon | Exploration Level |
|:------------:|:----------:|:------:|:----------------:|
| 0-500 | 45.2 | 0.30 -> 0.10 | High exploration |
| 500-1000 | 78.6 | 0.10 -> 0.04 | Moderate |
| 1000-2000 | 112.3 | 0.04 -> 0.01 | Low |
| 2000-3000 | 145.8 | 0.01 | Exploitation |
| 3000-4000 | 168.2 | 0.01 | Exploitation |
| 4000-5000 | 190.9 | 0.01 | Final |

The learning curve shows continuous improvement but is far from converging
to a useful policy. The best achieved reward (190.9) is only 16% of
the Baseline 2 reward (1,184.2).

## Convergence Analysis

Q-learning convergence requires visiting every state-action pair infinitely often.
With 88,368 states and 263 actions, this is impossible within 5,000 episodes
of 50 steps each (250,000 total steps).

The agent converges to a locally optimal policy within the visited states,
but this covers only a tiny fraction of the state space.

## Error Analysis

### Type I Error - Overestimation
The agent overestimates the value of rarely-visited states due to optimistic
initialization and insufficient negative samples.

### Type II Error - Underestimation
Good states that require complex multi-step sequences to reach are
never properly valued because the agent can't discover the sequence
within the exploration budget.

## Comparison: Model-Based vs Model-Free

| Aspect | Model-Based (Two-Step) | Model-Free (Q-Learning) |
|--------|:--------------------:|:---------------------:|
| Performance | $569.8/day | $190.9/episode |
| Computation | 0.24 ms/query | ~50 ms/episode (training) |
| State coverage | 100% (via statistics) | ~0.1% (visited) |
| Generalization | Strong (domain structure) | None (tabular) |
| Data efficiency | High (uses all data) | Low (on-policy only) |
| Optimality | Approximate | Local only |

## Recommendations for Improvement

1. **Function approximation**: Use Deep Q-Network (DQN) to generalize across states
2. **Experience replay**: Learn from historical transitions, not just on-policy
3. **Hierarchical RL**: Learn zone-level policies first, then refine with time
4. **Pretraining**: Initialize Q-values from model-based value function
5. **Reduced state space**: Cluster zones or discretize time more coarsely
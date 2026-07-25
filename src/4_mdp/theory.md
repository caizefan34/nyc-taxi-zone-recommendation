# Markov Decision Process for Taxi Zone Recommendation

## Theoretical Foundation

A Markov Decision Process (MDP) is defined by the tuple $(S, A, P, R, \gamma)$ where:
- **$S$**: State space (zone, weekday, time_slot)
- **$A$**: Action space (destination zone)
- **$P$**: Transition probability $P(s' | s, a)$
- **$R$**: Reward function $R(s, a)$
- **$\gamma$**: Discount factor

### Bellman Equation

The optimal value function satisfies the Bellman optimality equation:

$$V^*(s) = \max_{a \in A} \left[ R(s, a) + \gamma \sum_{s' \in S} P(s' | s, a) V^*(s') \right]$$

### Value Iteration

Value iteration converges to $V^*$ by repeatedly applying the Bellman backup:

$$V_{k+1}(s) = \max_{a \in A} \left[ R(s, a) + \gamma \sum_{s' \in S} P(s' | s, a) V_k(s') \right]$$

Convergence criterion: $||V_{k+1} - V_k||_\infty < \epsilon$

### Policy Extraction

Once $V^*$ is found, the optimal policy is:

$$\pi^*(s) = \arg\max_{a \in A} \left[ R(s, a) + \gamma \sum_{s' \in S} P(s' | s, a) V^*(s') \right]$$

## Differences from Two-Step Planning

| Aspect | Two-Step Planning | Full MDP Value Iteration |
|--------|------------------|------------------------|
| Horizon | 2 steps | Infinite (discounted) |
| Computation | O(K x Z) per query | O(|S| x |A|) per iteration |
| State eval | Online per query | Offline precomputation |
| Optimality | Approximate | Globally optimal |
| Memory | Module-level globals | Value table 263x336 |

## Time Complexity Analysis

- State space: |S| = 263 x 336 = 88,368
- Action space: |A| = 263
- Per iteration: O(|S| x |A|) = O(23M) operations
- Convergence: Typically 50-200 iterations
- Total precomputation: O(iterations x |S| x |A|)
- Online query: O(|A|) = O(263) (simple lookup)

## Practical Considerations

The full MDP is computationally expensive due to the large state space.
The current Two-Step Planning is a practical approximation that:
1. Only considers 100 candidate zones instead of all 263
2. Only looks 2 steps ahead instead of full horizon
3. Uses heuristic candidate selection
4. Achieves 0.24ms query time vs potentially slower MDP lookup

However, the full MDP would provide theoretically optimal recommendations
if the transition model is accurate enough.
# Methodology

## Algorithm Overview

We propose a **Two-Step Finite Horizon Planning** approach that extends single-step utility maximization by incorporating transition probabilities and discounted future value.

---

## Baseline 1: Hot Zone Ranking

The simplest strategy ranks zones by historical pickup demand for the matching weekday and time slot.

### Algorithm

```
Algorithm 1: Hot Zone Ranking
─────────────────────────────
Input: current_datetime, current_location_id
Output: Top-3 zone recommendations

1:  target_time ← next_half_hour(current_datetime)
2:  slot ← target_time.hour × 2 + target_time.minute ÷ 30
3:  weekday ← target_time.weekday()
4:  
5:  FOR each zone z ∈ {1, ..., 263}:
6:      score[z] ← pickup_count[weekday][slot][z]
7:  
8:  RETURN top-3 zones sorted by score (descending)
```

**Complexity**: $O(|\mathcal{Z}| \log |\mathcal{Z}|)$ for sorting

**Limitations**:
- Ignores competition among drivers
- Does not account for relocation cost
- Assumes all drivers can reach any zone instantly

---

## Baseline 2: Single-Step Utility

Improves upon Baseline 1 by incorporating both demand and travel cost.

### Algorithm

```
Algorithm 2: Single-Step Utility
─────────────────────────────────
Input: current_datetime, current_location_id
Output: Top-3 zone recommendations

1:  target_time ← next_half_hour(current_datetime)
2:  slot ← target_time.hour × 2 + target_time.minute ÷ 30
3:  weekday ← target_time.weekday()
4:  
5:  FOR each zone z ∈ {1, ..., 263}:
6:      demand ← pickup_count[weekday][slot][z]
7:      fare ← mean_fare[weekday][slot][z]
8:      travel_time ← dijkstra_matrix[current_zone][z]
9:      
10:     utility[z] ← (demand × fare) / (travel_time + 1)
11: 
12: RETURN top-3 zones sorted by utility (descending)
```

**Complexity**: $O(|\mathcal{Z}| \log |\mathcal{Z}|)$

**Improvements over Baseline 1**:
- Accounts for relocation time
- Balances demand vs. fare amount
- Penalizes distant zones

---

## Two-Step Finite Horizon Planning (Ours)

The core contribution: extends single-step utility by modeling the **expected future value** after both successful pickup and failure scenarios.

### Key Insight

A zone with high immediate utility may lead to poor future states (e.g., low-demand dropoff areas). By considering the **two-step value**, we can avoid myopic decisions.

### Value Function

For a candidate zone $z$ at arrival state $s' = (d', \text{slot}')$:

$$V(z, s') = p_s(z, s') \cdot \left[\bar{f}(z, s') + \gamma \cdot V_{\text{success}}(z, s')\right] + (1 - p_s(z, s')) \cdot \gamma \cdot V_{\text{fail}}(z, s')$$

where:

**Pickup probability**:
$$p_s(z, s') = \frac{D(z, s')}{D(z, s') + \lambda}$$

**Success value** (after pickup, weighted by dropoff distribution):
$$V_{\text{success}}(z, s') = \sum_{z'} P(z' | z) \cdot V_{\text{one-step}}(z', s'' )$$

where $s''$ is the state after trip duration.

**Failure value** (stay in zone, advance one slot):
$$V_{\text{fail}}(z, s') = V_{\text{one-step}}(z, s' + 1)$$

**One-step value**:
$$V_{\text{one-step}}(z, s) = p_s(z, s) \cdot \bar{f}(z, s)$$

### Full Algorithm

```
Algorithm 3: Two-Step Finite Horizon Planning
──────────────────────────────────────────────
Input: current_datetime, current_location_id
       demand[7][48][263], mean_fare[7][48][263]
       travel_time[263][263], transition_prob[263][263]
       mean_trip_duration[263]
       λ = 1.0, γ = 0.5, pool_size = 100
Output: Top-3 zone recommendations

// Phase 1: Compute baseline utility for all zones
1:  target_time ← next_half_hour(current_datetime)
2:  slot ← target_time.hour × 2 + target_time.minute ÷ 30
3:  weekday ← target_time.weekday()
4:  state ← weekday × 48 + slot
5:  
6:  FOR each zone z ∈ {0, ..., 262}:
7:      base_utility[z] ← demand[state][z] × mean_fare[state][z] 
8:                        / (travel_time[origin][z] + 1)
9:      arrival_slot[z] ← (state + ⌊travel_time[origin][z] / 30⌋) mod 336
10:
// Phase 2: Pre-select candidates by baseline utility
11: candidates ← top pool_size zones by base_utility
12: candidates ← candidates ∪ {origin_zone}
13:
// Phase 3: Compute two-step utility for candidates
14: FOR each z ∈ candidates:
15:     arr_state ← arrival_slot[z]
16:     arr_weekday ← arr_state ÷ 48
17:     arr_slot ← arr_state mod 48
18:     
19:     // Pickup probability
20:     d ← demand[arr_weekday][arr_slot][z]
21:     p_success ← d / (d + λ)
22:     
23:     // Expected fare
24:     f ← mean_fare[arr_weekday][arr_slot][z]
25:     
26:     // Success value: weighted by dropoff distribution
27:     future_success ← 0
28:     FOR each dropoff_zone z' where transition_prob[z][z'] > 0:
29:         trip_slots ← ⌊mean_trip_duration[z] / 30⌉
30:         next_state ← (arr_state + 1 + trip_slots) mod 336
31:         next_weekday ← next_state ÷ 48
32:         next_slot ← next_state mod 48
33:         v_drop ← one_step_value(z', next_weekday, next_slot)
34:         future_success ← future_success + transition_prob[z][z'] × v_drop
35:     
36:     // Failure value: stay at z, advance 1 slot
37:     next_state_fail ← (arr_state + 1) mod 336
38:     fail_weekday ← next_state_fail ÷ 48
39:     fail_slot ← next_state_fail mod 48
40:     future_fail ← one_step_value(z, fail_weekday, fail_slot)
41:     
42:     // Two-step utility
43:     u ← p_success × (f + γ × future_success) 
44:         + (1 - p_success) × γ × future_fail
45:     
46:     // Apply relocation cost
47:     IF z == origin:
48:         move_cost ← 0
49:     ELSE:
50:         move_cost ← travel_time[origin][z]
51:     
52:     move_slots ← ⌊move_cost / 30⌉
53:     two_step_utility[z] ← u / (move_slots + 1)
54:
55: RETURN top-3 zones sorted by two_step_utility (descending)
```

### Complexity Analysis

| Phase | Operations | Complexity |
|-------|-----------|------------|
| Baseline utility | $O(|\mathcal{Z}|)$ | Linear |
| Candidate selection | $O(|\mathcal{Z}| \log K)$ | Partial sort |
| Two-step computation | $O(K \times |\mathcal{Z}|)$ | For each candidate, iterate dropoff distribution |
| Final ranking | $O(|\mathcal{Z}| \log |\mathcal{Z}|)$ | Sort all zones |

**Total**: $O(K \times |\mathcal{Z}| + |\mathcal{Z}| \log |\mathcal{Z}|)$ where $K = 100$ is the candidate pool size.

**Practical latency**: ~0.24 ms per query on modern hardware.

---

## Hyperparameter Selection

### Grid Search

We perform grid search over:
- $\lambda \in \{0.5, 1.0, 2.0\}$: pickup probability half-saturation
- $\gamma \in \{0.25, 0.5, 0.75\}$: discount factor for future utility

### Selection Criteria

Parameters are selected by:
1. **Primary**: NDCG@3 on public validation queries
2. **Secondary**: Hit@3 (tie-breaker)
3. **Tertiary**: Average recommendation latency

### Results

| λ | γ | NDCG@3 | Hit@3 | Latency (ms) |
|---|---|--------|-------|--------------|
| 0.5 | 0.25 | 0.9976 | 0.9987 | 0.23 |
| 0.5 | 0.50 | 0.9977 | 0.9988 | 0.24 |
| 0.5 | 0.75 | 0.9975 | 0.9986 | 0.25 |
| **1.0** | **0.25** | 0.9977 | 0.9988 | 0.23 |
| **1.0** | **0.50** | **0.9978** | **0.9988** | **0.24** |
| 1.0 | 0.75 | 0.9976 | 0.9987 | 0.25 |
| 2.0 | 0.25 | 0.9975 | 0.9986 | 0.23 |
| 2.0 | 0.50 | 0.9976 | 0.9987 | 0.24 |
| 2.0 | 0.75 | 0.9974 | 0.9985 | 0.25 |

**Selected**: $\lambda = 1.0, \gamma = 0.5$

---

## Transition Probability Estimation

### OD Matrix Construction

Transition probabilities are estimated from the cleaned training data:

$$P(z' | z) = \frac{N(z \rightarrow z')}{\sum_{z''} N(z \rightarrow z'')}$$

where $N(z \rightarrow z')$ is the count of trips from zone $z$ to zone $z'$ in the training set.

### Sparsity Handling

For zones with limited historical data, we apply hierarchical smoothing:
1. Use zone-specific transition distribution if $N(z) \geq 30$
2. Fall back to weekday-level aggregate if $N(z, d) \geq 10$
3. Fall back to global distribution otherwise

In practice, the training set contains 2.24M trips, providing sufficient coverage for most zones.

---

## Comparison with Reinforcement Learning

### Q-Learning Baseline

We also implement a tabular Q-learning agent as a model-free baseline:

**State**: $(zone, weekday, slot) \in \mathcal{S}$

**Action**: Destination zone $z \in \{1, \ldots, 263\}$

**Reward**: $R = \text{fare} - \text{idle\_cost}$

**Update rule**:
$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[R + \gamma \max_{a'} Q(s', a') - Q(s, a)\right]$$

**Hyperparameters**:
- Learning rate: $\alpha = 0.1$
- Discount factor: $\gamma = 0.9$
- Exploration: $\epsilon = 0.3$ with decay $0.995$
- Episodes: 5,000
- Max steps per episode: 50

**Results**:
- Q-table size: 22,278 entries
- Evaluation (200 episodes): Avg reward = 190.9
- Baseline 2 comparison: Avg reward = 1,184.2

**Analysis**: Q-learning significantly underperforms due to:
1. **State space too large**: 88,368 states with only 22,278 visited
2. **Insufficient exploration**: Tabular methods struggle with sparse rewards
3. **No generalization**: Each state learned independently

This motivates our model-based approach which leverages domain structure.

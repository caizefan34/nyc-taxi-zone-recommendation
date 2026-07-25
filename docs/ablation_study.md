# Ablation Study

## Experimental Setup

We conduct ablation experiments to isolate the contribution of each component in our two-step planning framework. All experiments use the same public validation set of 3,360 queries.

---

## Experiment 1: Effect of Future Value Modeling

### Configuration

| Variant | Description |
|---------|-------------|
| **Single-step (γ=0)** | Only considers immediate reward; equivalent to Baseline 2 with pickup probability |
| **Two-step (γ=0.5)** | Full model with discounted future value (ours) |
| **Two-step (γ=0.75)** | Higher discount on future value |

### Results

| Variant | NDCG@3 | Hit@3 | Top-1 Utility | Avg Daily Fare |
|---------|--------|-------|---------------|----------------|
| Single-step (γ=0) | 0.9972 | 0.9984 | 27.42 | $549.0 |
| **Two-step (γ=0.5)** | **0.9978** | **0.9988** | **27.75** | **$569.8** |
| Two-step (γ=0.75) | 0.9976 | 0.9987 | 27.61 | $562.3 |

### Analysis

- **Single-step** achieves strong static metrics but underperforms in simulation because it ignores post-trip state quality.
- **Two-step (γ=0.5)** balances immediate reward and future value, achieving the best trade-off.
- **Two-step (γ=0.75)** over-weights future value, leading to recommendations that are good long-term but suboptimal for the immediate next trip.

---

## Experiment 2: Effect of Transition Probability Modeling

### Configuration

| Variant | Description |
|---------|-------------|
| **Uniform dropoff** | Assumes equal probability of dropping off at any zone |
| **Empirical dropoff** | Uses observed OD transition probabilities from training data |
| **Empirical + duration** | Also accounts for mean trip duration per zone |

### Results

| Variant | NDCG@3 | Hit@3 | Avg Daily Fare |
|---------|--------|-------|----------------|
| Uniform dropoff | 0.9974 | 0.9986 | $558.2 |
| Empirical dropoff | 0.9977 | 0.9988 | $565.1 |
| **Empirical + duration** | **0.9978** | **0.9988** | **$569.8** |

### Analysis

- **Uniform dropoff** provides a modest improvement over single-step by acknowledging that dropoff location matters.
- **Empirical dropoff** captures real-world patterns (e.g., airport trips, suburban returns) and improves simulation performance.
- **Empirical + duration** further refines the model by accounting for time spent during trips, which affects the next available time slot.

---

## Experiment 3: Effect of Candidate Pool Size

### Configuration

We vary the candidate pool size $K$ (number of zones considered for two-step computation) from 10 to all 263 zones.

| Pool Size $K$ | NDCG@3 | Hit@3 | Latency (ms) |
|---------------|--------|-------|--------------|
| 10 | 0.9968 | 0.9982 | 0.04 |
| 50 | 0.9975 | 0.9986 | 0.12 |
| **100** | **0.9978** | **0.9988** | **0.24** |
| 150 | 0.9978 | 0.9988 | 0.36 |
| 263 (all) | 0.9978 | 0.9988 | 0.62 |

### Analysis

- **K=10**: Too restrictive; misses high-value zones that are not in the top baseline candidates.
- **K=50**: Good performance with low latency; suitable for real-time systems with strict latency constraints.
- **K=100**: Near-optimal performance with acceptable latency; our default choice.
- **K=263**: No improvement over K=100 but 2.5× slower; confirms that low-utility zones rarely contribute to optimal recommendations.

**Conclusion**: $K=100$ provides the best performance-latency trade-off.

---

## Experiment 4: Effect of Relocation Cost Normalization (λ)

### Configuration

The half-saturation parameter $\lambda$ controls the shape of the pickup probability function:

$$p_s(z, s) = \frac{D(z, s)}{D(z, s) + \lambda}$$

| λ | Interpretation | NDCG@3 | Hit@3 |
|---|---------------|--------|-------|
| 0.5 | High sensitivity to demand differences | 0.9977 | 0.9988 |
| **1.0** | **Balanced (default)** | **0.9978** | **0.9988** |
| 2.0 | Low sensitivity (more uniform probabilities) | 0.9976 | 0.9987 |

### Analysis

- **λ=0.5**: Amplifies differences between high-demand and low-demand zones; slightly overconfident in top zones.
- **λ=1.0**: Provides a smooth, balanced probability curve; best overall performance.
- **λ=2.0**: Compresses probability differences; treats zones more uniformly, losing discriminative power.

---

## Experiment 5: Data Cleaning Impact

### Configuration

| Variant | Training Data | Validation Data |
|---------|:------------:|:---------------:|
| **Full cleaning (ours)** | 2,243,804 rows | 688,250 rows |
| No cleaning | 2,346,719 rows | 725,968 rows |
| Basic cleaning (no outliers) | 2,289,618 rows | 706,023 rows |

### Results

| Variant | NDCG@3 | Hit@3 | Avg Daily Fare |
|---------|--------|-------|----------------|
| No cleaning | 0.9965 | 0.9979 | $541.2 |
| Basic cleaning | 0.9973 | 0.9985 | $558.7 |
| **Full cleaning** | **0.9978** | **0.9988** | **$569.8** |

### Analysis

- **No cleaning**: Outliers (extreme fares, impossible speeds, invalid zones) distort demand estimates and transition probabilities.
- **Basic cleaning**: Removes invalid records but retains fare/duration outliers.
- **Full cleaning**: Removes all anomalous records, leading to more accurate demand and transition estimates.

**Key insight**: Data quality is as important as algorithm design. Cleaning removes ~4% of records but improves simulation revenue by 5.2%.

---

## Summary

| Component | Contribution to NDCG@3 | Contribution to Daily Fare |
|-----------|:----------------------:|:--------------------------:|
| Data cleaning | +0.0013 | +$28.6 |
| Two-step planning (γ>0) | +0.0006 | +$20.8 |
| Transition probabilities | +0.0003 | +$11.6 |
| Trip duration modeling | +0.0001 | +$4.7 |
| Candidate pool K=100 | +0.0010 | — |
| **Total (ours)** | **0.9978** | **$569.8** |

All components contribute positively, with data cleaning and two-step planning being the most impactful.

# Problem Formulation

## Spatial-Temporal Taxi Zone Recommendation

### Definition

Given a taxi driver's current state $(z_t, t)$ where $z_t \in \{1, 2, \ldots, 263\}$ is the current zone and $t$ is the current timestamp, the goal is to recommend a set of **top-3 zones** $R = \{z_1^{\star}, z_2^{\star}, z_3^{\star}\}$ that maximizes the driver's expected cumulative revenue over a planning horizon.

### State Space

The state space is defined as:

$$\mathcal{S} = \mathcal{Z} \times \mathcal{T}$$

where:
- $\mathcal{Z} = \{1, 2, \ldots, 263\}$: NYC taxi zones (TLC definition)
- $\mathcal{T} = \{(d, s) : d \in \{0,\ldots,6\}, s \in \{0,\ldots,47\}\}$: discretized time with weekday $d$ and half-hour slot $s$

This yields $|\mathcal{S}| = 263 \times 336 = 88{,}368$ distinct states.

### Action Space

At each state, the driver chooses a destination zone $a \in \mathcal{Z}$ to relocate to. The action space is the full set of 263 zones.

### Objective

Find a policy $\pi: \mathcal{S} \rightarrow \mathcal{Z}^3$ that maximizes:

$$\mathbb{E}\left[\sum_{k=0}^{K} \gamma^k \cdot R(s_k, a_k)\right]$$

where:
- $R(s_k, a_k)$ is the immediate reward (expected fare) at step $k$
- $\gamma \in [0, 1]$ is the discount factor
- $K$ is the planning horizon

### Reward Model

The reward for relocating to zone $z$ from state $s = (d, \text{slot})$ is:

$$R(s, z) = p_{\text{pickup}}(z, s) \cdot \bar{f}(z, s)$$

where:
- $p_{\text{pickup}}(z, s) = \frac{D(z, s)}{D(z, s) + \lambda}$ is the pickup probability with half-saturation parameter $\lambda$
- $D(z, s)$ is the historical pickup demand at zone $z$ during slot $s$
- $\bar{f}(z, s)$ is the mean fare amount for trips originating at zone $z$ during slot $s$

### Transition Dynamics

After a successful pickup at zone $z$, the driver transitions to the dropoff zone $z'$ with probability:

$$P(z' | z) = \frac{N(z \rightarrow z')}{\sum_{z''} N(z \rightarrow z'')}$$

where $N(z \rightarrow z')$ is the historical count of trips from zone $z$ to zone $z'$.

### Relocation Cost

Moving from zone $z_i$ to zone $z_j$ incurs a time cost $\tau(z_i, z_j)$ computed via Dijkstra's shortest path on the road network. The effective utility is discounted by:

$$U_{\text{effective}}(z_j) = \frac{U(z_j)}{\lfloor \tau(z_i, z_j) / 30 \rfloor + 1}$$

### Evaluation Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **NDCG@3** | $\frac{1}{|Q|}\sum_{q} \frac{DCG_q}{IDCG_q}$ | Normalized discounted cumulative gain |
| **Hit@3** | $\frac{1}{|Q|}\sum_{q} \mathbb{1}[\text{argmax}_z U_q(z) \in R_q]$ | Fraction of queries where top-1 ideal zone is in recommendations |
| **Top-1 Utility** | $\frac{1}{|Q|}\sum_{q} U_q(r_1^{(q)})$ | Mean reference utility of the top-ranked recommendation |
| **Avg Daily Fare** | $\frac{1}{N}\sum_{i=1}^{N} F_i$ | Mean total fare earned per simulated day |

### Constraints

- **Real-time**: Recommendation latency must be < 10 ms per query
- **Data**: Only historical trip data available (no real-time demand signals)
- **Stationarity**: Demand patterns assumed to follow weekly seasonality

# Methodology

## Problem definition

A query contains a current time `t` and taxi zone `o`. A strategy returns three distinct destination zones in ranked order.

The repository uses 263 TLC zones and 48 half-hour slots per weekday, producing 336 recurring weekly time states.

## Temporal protocol

- Training: 2023-01-01 through 2023-01-24.
- Public validation: 2023-01-25 through 2023-01-31.
- A trip is retained only when pickup and dropoff both satisfy the corresponding boundary.
- Demand, fare, travel time, OD transitions, and duration statistics are built from training data only.

The public validation labels may be used for a pre-declared parameter grid, but final scientific evaluation requires an untouched later test period. The audit utilities provide expanding rolling-window splits for multi-month data.

## Data cleaning

The executable rules remove:

- out-of-boundary or non-positive-duration trips;
- missing required fields;
- invalid pickup/dropoff zone IDs;
- fare outside $0–$200;
- duration outside 1–240 minutes;
- distance outside 0.1–100 miles when available;
- implied speed above 80 mph;
- duplicate trip keys.

The cleaning command can now split the official monthly parquet into chronological train and validation inputs automatically.

## Baseline 1: hot zones

For the strictly next half-hour boundary:

\[
U_{B1}(z,t)=D(z,\operatorname{next}(t)).
\]

The three largest training pickup counts are returned.

## Baseline 2: single-step utility

\[
U_{B2}(o,z,t)=\frac{D(z,t)\bar f(z,t)}{T(o,z)+1}.
\]

`T` is the directed Dijkstra travel-time matrix estimated from training OD durations.

## Finite-horizon continuation model

Pickup probability is a scenario model, not an empirically identified probability:

\[
p(s,z)=\frac{D(s,z)}{D(s,z)+240}.
\]

The terminal one-step value is

\[
V_1(s,z)=p(s,z)\bar f(s,z).
\]

For `h > 1`:

\[
V_h(s,z)=p(s,z)\left[\bar f(s,z)+\gamma\sum_{z'}P(z'\mid z)V_{h-1}(s+1+\tau_z,z')\right]
 +(1-p(s,z))\gamma V_{h-1}(s+1,z).
\]

The initial action is normalized by rounded relocation slots. The continuation policy waits in the reached zone; it does not optimize a new relocation action. This is truncated fixed-policy lookahead, not full finite-horizon Bellman optimality.

## Corrected model-based MDP

The MDP module separately implements synchronous Bellman optimality backups. An action relocates from the current zone to a candidate zone. After arrival:

- success earns fare, advances one pickup slot plus passenger duration, and moves to an OD-sampled dropoff zone;
- failure earns zero, advances one pickup slot, and stays in the candidate zone.

Unlike the earlier implementation, every pickup attempt advances time and policy extraction depends on the current origin.

## Static evaluation

The public answer for each query is a 263-zone reference-utility vector. Metrics are:

\[
NDCG@3=\frac{DCG@3}{IDCG@3}
\]

and Hit@3, which checks whether the reference-optimal zone appears in the returned Top-3.

These metrics diagnose agreement with the reference objective. They do not measure observed driver behavior or causal revenue.

## Rollout evaluation

The fixed simulator samples one executable recommendation with rank weights 0.6/0.3/0.1, relocates one driver, applies `n/(n+40)` pickup success in a concrete validation day/slot/zone cell, and samples a historical trip on success.

It omits competition, demand depletion, congestion, supply response, and equilibrium. Rollout values must be interpreted as within-simulator comparisons.

## Statistical analysis

Strategies are compared with the same random seeds. Reports include:

- mean and standard deviation;
- paired bootstrap 95% confidence interval;
- paired t-test;
- Wilcoxon signed-rank test;
- Cohen's dz.

These quantify simulator Monte Carlo uncertainty only. Real-market inference requires day/week blocking and held-out temporal periods.

## Counterfactual evaluation

IPS, SNIPS, and doubly robust estimators are implemented and tested. They are not applied to TLC trips because the data lack logged recommendation actions and behavior propensities. Reporting a numeric OPE value without those fields would be invalid.

## Exposure analysis

Rank-weighted exposure is aggregated with the rollout weights. The report includes coverage, Gini, entropy/effective zone count, airport exposure, Manhattan exposure, and premium-fare-zone exposure.

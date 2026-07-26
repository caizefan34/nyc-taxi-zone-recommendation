# Model-Based MDP for Taxi Repositioning

The corrected implementation lives in `src/mdp/model_based.py`; the `src/4_mdp` path is a compatibility wrapper.

## State and action

- State: current zone and recurring weekly half-hour slot.
- Action: relocation destination zone.

## Transition

After relocation to action zone `a`:

- pickup succeeds with scenario probability `D/(D+240)`;
- success earns mean fare, advances one pickup-attempt slot plus passenger duration, and transitions through `P(dropoff|a)`;
- failure earns zero, advances one pickup-attempt slot, and remains in `a`.

## Bellman backup

$$
Q(s,a)=p_a\left[f_a+\gamma\sum_{s'}P_{success}(s'\mid s,a)V(s')\right]
 +(1-p_a)\gamma V(s'_{failure}),
$$

$$
V_{k+1}(s)=\max_a Q_k(s,a).
$$

Backups are synchronous. Time advances after every pickup attempt, including stay actions. Policy extraction uses the actual current origin and action-specific relocation time.

## Validity boundary

This is optimal only for the estimated single-driver model. It is not globally optimal for the real taxi market because supply, competition, congestion, demand depletion, and model uncertainty are absent.

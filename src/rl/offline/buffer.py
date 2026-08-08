"""Offline replay buffer for historical trajectory data.

Stores (state, action, reward, next_state, done) transitions
collected from the v2 simulator or real data.

Enhanced fields:
- trajectory_id: Identifies which episode/trajectory a transition belongs to
- timestamp: Simulation timestamp for the transition
- behavior_prob: Probability of the chosen action under the behavior policy
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class Trajectory:
    """Single trajectory of (state, action, reward) steps."""
    states: np.ndarray       # (T, state_dim)
    actions: np.ndarray      # (T,)
    rewards: np.ndarray      # (T,)
    dones: np.ndarray        # (T,)
    next_states: np.ndarray  # (T, state_dim)
    trajectory_id: int = 0   # Unique trajectory identifier
    timestamps: np.ndarray | None = None  # (T,) optional timestamps
    behavior_probs: np.ndarray | None = None  # (T,) logged action propensities


class OfflineBuffer:
    """Fixed-capacity buffer for offline RL transitions.

    Stores transitions collected from the v2 dynamic simulator
    for offline policy learning and evaluation.

    Enhanced with trajectory_id, timestamp, and behavior_policy_probability
    fields for more detailed OPE and trajectory analysis.
    """

    def __init__(self, capacity: int = 100_000, state_dim: int = 7, seed: int = 42) -> None:
        self.capacity = capacity
        self.state_dim = state_dim
        self.rng = np.random.default_rng(seed)

        self.states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int32)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)

        # Enhanced fields
        self.trajectory_ids = np.zeros(capacity, dtype=np.int32)
        self.timestamps = np.zeros(capacity, dtype=np.float64)
        self.behavior_probs = np.zeros(capacity, dtype=np.float32)

        self._size = 0
        self._index = 0

    @property
    def size(self) -> int:
        return self._size

    @property
    def fraction_filled(self) -> float:
        return self._size / self.capacity

    def add(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        *,
        trajectory_id: int = 0,
        timestamp: float | None = None,
        behavior_prob: float = 1.0,
    ) -> None:
        """Add a single transition to the buffer.

        Args:
            state: Current state vector.
            action: Chosen action (zone ID).
            reward: Net reward for this transition.
            next_state: Resulting state.
            done: Whether the episode terminated.
            trajectory_id: Identifier for the trajectory/episode.
            timestamp: Simulation timestamp (Unix time or relative).
            behavior_prob: Probability of this action under behavior policy.
        """
        if not 0.0 < behavior_prob <= 1.0:
            raise ValueError("behavior_prob must be in (0, 1]")
        state_array = np.asarray(state, dtype=np.float32).ravel()
        next_state_array = np.asarray(next_state, dtype=np.float32).ravel()
        if state_array.shape != (self.state_dim,) or next_state_array.shape != (self.state_dim,):
            raise ValueError(f"state vectors must have shape ({self.state_dim},)")

        idx = self._index % self.capacity
        self.states[idx] = state_array
        self.actions[idx] = int(action)
        self.rewards[idx] = float(reward)
        self.next_states[idx] = next_state_array
        self.dones[idx] = float(done)

        # Enhanced fields
        self.trajectory_ids[idx] = int(trajectory_id)
        self.timestamps[idx] = float(timestamp) if timestamp is not None else float(self._index)
        self.behavior_probs[idx] = float(behavior_prob)

        self._index += 1
        self._size = min(self._size + 1, self.capacity)

    def add_trajectory(self, traj: Trajectory) -> None:
        """Add all transitions from a trajectory."""
        for i in range(len(traj.rewards)):
            ts = float(traj.timestamps[i]) if traj.timestamps is not None else None
            behavior_prob = float(traj.behavior_probs[i]) if traj.behavior_probs is not None else 1.0
            self.add(
                traj.states[i], int(traj.actions[i]), float(traj.rewards[i]),
                traj.next_states[i], bool(traj.dones[i]),
                trajectory_id=traj.trajectory_id,
                timestamp=ts,
                behavior_prob=behavior_prob,
            )

    def _ordered_indices(self) -> np.ndarray:
        """Return stored transitions from oldest to newest."""
        if self._size < self.capacity:
            return np.arange(self._size)
        start = self._index % self.capacity
        return np.concatenate((np.arange(start, self.capacity), np.arange(0, start)))

    def as_ordered_dict(self) -> dict[str, np.ndarray]:
        """Return all transitions in logical insertion order."""
        indices = self._ordered_indices()
        return {
            "states": self.states[indices].copy(),
            "actions": self.actions[indices].copy(),
            "rewards": self.rewards[indices].copy(),
            "next_states": self.next_states[indices].copy(),
            "dones": self.dones[indices].copy(),
            "trajectory_ids": self.trajectory_ids[indices].copy(),
            "timestamps": self.timestamps[indices].copy(),
            "behavior_probs": self.behavior_probs[indices].copy(),
        }

    def sample(self, batch_size: int) -> dict[str, np.ndarray]:
        """Sample a random batch of transitions.

        Returns dict with keys: states, actions, rewards, next_states, dones,
        trajectory_ids, timestamps, behavior_probs.
        """
        if self._size < batch_size:
            raise ValueError(f"buffer has {self._size} transitions, need {batch_size}")
        indices = self.rng.integers(0, self._size, size=batch_size)
        return {
            "states": self.states[indices],
            "actions": self.actions[indices],
            "rewards": self.rewards[indices],
            "next_states": self.next_states[indices],
            "dones": self.dones[indices],
            "trajectory_ids": self.trajectory_ids[indices],
            "timestamps": self.timestamps[indices],
            "behavior_probs": self.behavior_probs[indices],
        }

    def clear(self) -> None:
        self._size = 0
        self._index = 0

    def collect_from_simulator(
        self,
        simulator: object,
        episodes: int = 100,
        max_steps: int = 100,
        *,
        state_fn: callable,
        reward_fn: callable,
        policy_fn: callable,
    ) -> None:
        """Collect transitions by running a policy in a simulator.

        Args:
            simulator: Object with `state` attribute and `step(action)` method.
            episodes: Number of episodes to run.
            max_steps: Max steps per episode.
            state_fn: Extracts state vector from simulator state.
            reward_fn: Extracts reward from step result.
            policy_fn: Maps state to action.
        """

        for ep in range(episodes):
            sim = simulator
            if hasattr(sim, "run"):
                sim.run(datetime(2023, 1, 25), datetime(2023, 2, 1))
            state = state_fn(sim) if callable(state_fn) else np.zeros(self.state_dim)
            for step in range(max_steps):
                action = policy_fn(state)
                reward = reward_fn(sim, action) if callable(reward_fn) else 0.0
                next_state = state_fn(sim) if callable(state_fn) else state
                done = step == max_steps - 1
                self.add(state, action, reward, next_state, done, trajectory_id=ep)
                state = next_state
                if done:
                    break

    def collect_trajectories_from_v2(
        self,
        simulator,
        episodes: int = 20,
        *,
        strategy=None,
    ) -> None:
        """Collect realistic transitions from the v2 DynamicSimulator.

        Uses the simulator's `run()` method with `on_transition` callback
        to record real (state, action, reward, next_state, done) transitions.

        State vector (7-dim):
          [0] zone_id / 263.0          - normalized location
          [1] (hour*60+min)/1440.0     - normalized time of day
          [2] driver_count_in_zone / total_taxis - supply density
          [3] zone.effective_demand / 200.0       - normalized demand
          [4] zone.pickup_probability             - pickup chance
          [5] driver_count_in_zone / max(1, zone.trips_remaining) - competition
          [6] zone.traffic_multiplier / 2.0       - normalized traffic

        Args:
            simulator: DynamicSimulator instance with `run()` method.
            episodes: Number of simulation runs.
            strategy: Driver strategy function (time, zone, state) -> zone.
        """

        import numpy as np

        ZONE_COUNT = 263

        def _extract_state(env, driver_id, *, zone_id=None, current_time=None):
            d = env.drivers[driver_id]
            zone_id = d.location_zone if zone_id is None else zone_id
            current_time = d.current_time if current_time is None else current_time
            z = env.zones[zone_id]
            supply = env.driver_count_in_zone(zone_id)
            return np.array([
                zone_id / ZONE_COUNT,
                (current_time.hour * 60 + current_time.minute) / 1440.0,
                supply / max(1, env.total_taxis),
                min(z.effective_demand / 200.0, 1.0),
                z.pickup_probability,
                supply / max(1, z.trips_remaining),
                z.traffic_multiplier / 2.0,
            ], dtype=np.float32)

        for ep in range(episodes):
            collected: dict[int, list[tuple[np.ndarray, int, float, np.ndarray, bool, float, float]]] = {}

            def _transition_cb(
                driver_id,
                action_zone,
                reward,
                next_zone,
                done,
                decision_time,
                origin_zone,
                behavior_prob,
                next_time,
            ):
                env = simulator.state
                if env is None:
                    return
                state = _extract_state(
                    env,
                    driver_id,
                    zone_id=origin_zone,
                    current_time=decision_time,
                )
                next_state = _extract_state(
                    env,
                    driver_id,
                    zone_id=next_zone,
                    current_time=next_time,
                )
                collected.setdefault(driver_id, []).append(
                    (
                        state,
                        action_zone,
                        reward,
                        next_state,
                        done,
                        decision_time.timestamp(),
                        behavior_prob,
                    )
                )

            simulator.run(
                datetime(2023, 1, 25),
                datetime(2023, 2, 1),
                strategy=strategy,
                on_transition=_transition_cb,
            )

            driver_count = simulator.config.driver_count
            for driver_id in sorted(collected):
                transitions = collected[driver_id]
                trajectory_id = ep * driver_count + driver_id
                for index, (state, action, reward, next_state, done, ts, behavior_prob) in enumerate(
                    transitions
                ):
                    is_terminal = done or index == len(transitions) - 1
                    self.add(
                        state,
                        action,
                        reward,
                        next_state,
                        is_terminal,
                        trajectory_id=trajectory_id,
                        timestamp=ts,
                        behavior_prob=behavior_prob,
                    )

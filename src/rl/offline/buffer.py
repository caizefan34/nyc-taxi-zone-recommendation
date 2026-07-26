"""Offline replay buffer for historical trajectory data.

Stores (state, action, reward, next_state, done) transitions
collected from the v2 simulator or real data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Trajectory:
    """Single trajectory of (state, action, reward) steps."""
    states: np.ndarray       # (T, state_dim)
    actions: np.ndarray      # (T,)
    rewards: np.ndarray      # (T,)
    dones: np.ndarray        # (T,)
    next_states: np.ndarray  # (T, state_dim)


class OfflineBuffer:
    """Fixed-capacity buffer for offline RL transitions.

    Stores transitions collected from the v2 dynamic simulator
    for offline policy learning and evaluation.
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
    ) -> None:
        """Add a single transition to the buffer."""
        idx = self._index % self.capacity
        self.states[idx] = np.asarray(state, dtype=np.float32).ravel()
        self.actions[idx] = int(action)
        self.rewards[idx] = float(reward)
        self.next_states[idx] = np.asarray(next_state, dtype=np.float32).ravel()
        self.dones[idx] = float(done)
        self._index += 1
        self._size = min(self._size + 1, self.capacity)

    def add_trajectory(self, traj: Trajectory) -> None:
        """Add all transitions from a trajectory."""
        for i in range(len(traj.rewards)):
            self.add(
                traj.states[i], int(traj.actions[i]), float(traj.rewards[i]),
                traj.next_states[i], bool(traj.dones[i]),
            )

    def sample(self, batch_size: int) -> dict[str, np.ndarray]:
        """Sample a random batch of transitions.

        Returns dict with keys: states, actions, rewards, next_states, dones.
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
            simulator: Object with ``state`` attribute and ``step(action)`` method.
            episodes: Number of episodes to run.
            max_steps: Max steps per episode.
            state_fn: Extracts state vector from simulator state.
            reward_fn: Extracts reward from step result.
            policy_fn: Maps state to action.
        """
        from datetime import datetime

        for ep in range(episodes):
            sim = simulator
            if hasattr(sim, "run"):
                # DynamicSimulator: use run()
                sim.run(datetime(2023, 1, 25), datetime(2023, 2, 1))
            state = state_fn(sim) if callable(state_fn) else np.zeros(self.state_dim)
            for step in range(max_steps):
                action = policy_fn(state)
                reward = reward_fn(sim, action) if callable(reward_fn) else 0.0
                next_state = state_fn(sim) if callable(state_fn) else state
                done = step == max_steps - 1
                self.add(state, action, reward, next_state, done)
                state = next_state
                if done:
                    break

    def collect_trajectories_from_v2(
        self,
        simulator,
        episodes: int = 20,
        *,
        strategy = None,
    ) -> None:
        """Collect realistic transitions from the v2 DynamicSimulator.

        Uses the simulator's ``run()`` method with ``on_transition`` callback
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
            simulator: DynamicSimulator instance with ``run()`` method.
            episodes: Number of simulation runs.
            strategy: Driver strategy function (time, zone, state) -> zone.
        """
        from datetime import datetime

        import numpy as np

        ZONE_COUNT = 263

        def _extract_state(env, driver_id):
            d = env.drivers[driver_id]
            z = env.zones[d.location_zone]
            supply = env.driver_count_in_zone(d.location_zone)
            return np.array([
                d.location_zone / ZONE_COUNT,
                (d.current_time.hour * 60 + d.current_time.minute) / 1440.0,
                supply / max(1, env.total_taxis),
                min(z.effective_demand / 200.0, 1.0),
                z.pickup_probability,
                supply / max(1, z.trips_remaining),
                z.traffic_multiplier / 2.0,
            ], dtype=np.float32)

        for ep in range(episodes):
            collected = []

            def _transition_cb(driver_id, action_zone, reward, next_zone, done):
                env = simulator.state
                if env is None:
                    return
                state = _extract_state(env, driver_id)
                next_state = np.array([
                    next_zone / ZONE_COUNT,
                    (env.current_time.hour * 60 + env.current_time.minute) / 1440.0,
                    env.driver_count_in_zone(next_zone) / max(1, env.total_taxis),
                    min(env.zones[next_zone].effective_demand / 200.0, 1.0),
                    env.zones[next_zone].pickup_probability,
                    env.driver_count_in_zone(next_zone) / max(1, env.zones[next_zone].trips_remaining),
                    env.zones[next_zone].traffic_multiplier / 2.0,
                ], dtype=np.float32)
                collected.append((state, action_zone, reward, next_state, done))

            simulator.run(
                datetime(2023, 1, 25),
                datetime(2023, 2, 1),
                strategy=strategy,
                on_transition=_transition_cb,
            )

            for state, action, reward, next_state, done in collected:
                self.add(state, action, reward, next_state, done)

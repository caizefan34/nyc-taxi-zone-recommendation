"""Minimal reproducible DQN and Double-DQN implementation in PyTorch."""
from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class DQNConfig:
    """Optimization and exploration settings shared by both baselines."""

    gamma: float = 0.99
    learning_rate: float = 1e-3
    batch_size: int = 64
    replay_capacity: int = 20_000
    learning_starts: int = 500
    target_update_interval: int = 250
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay_steps: int = 10_000
    gradient_clip: float = 10.0
    hidden_sizes: tuple[int, ...] = (128, 128)

    def __post_init__(self) -> None:
        if not 0.0 <= self.gamma <= 1.0:
            raise ValueError("gamma must be in [0, 1]")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")
        if self.batch_size <= 0 or self.replay_capacity < self.batch_size:
            raise ValueError("replay_capacity must be at least batch_size")
        if self.learning_starts < self.batch_size:
            raise ValueError("learning_starts must be at least batch_size")


class QNetwork(nn.Module):
    """Fully connected action-value network."""

    def __init__(self, observation_size: int, action_count: int, *, hidden_sizes: tuple[int, ...]) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        input_size = observation_size
        for hidden_size in hidden_sizes:
            layers.extend((nn.Linear(input_size, hidden_size), nn.ReLU()))
            input_size = hidden_size
        layers.append(nn.Linear(input_size, action_count))
        self.network = nn.Sequential(*layers)

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.network(observations)


def select_bootstrap_values(
    online_values: torch.Tensor,
    target_values: torch.Tensor,
    action_mask: torch.Tensor,
    *,
    double_dqn: bool,
) -> torch.Tensor:
    """Apply standard or Double-DQN action selection with invalid actions masked."""
    has_valid_action = action_mask.any(dim=1)
    masked_target = target_values.masked_fill(~action_mask, -torch.inf)
    if not double_dqn:
        bootstrap = masked_target.max(dim=1).values
    else:
        masked_online = online_values.masked_fill(~action_mask, -torch.inf)
        selected_actions = masked_online.argmax(dim=1, keepdim=True)
        bootstrap = masked_target.gather(1, selected_actions).squeeze(1)
    return torch.where(has_valid_action, bootstrap, torch.zeros_like(bootstrap))


class ReplayBuffer:
    """Fixed-size transition replay with action masks."""

    def __init__(self, capacity: int, observation_size: int, action_count: int) -> None:
        self.capacity = capacity
        self.observations = np.empty((capacity, observation_size), dtype=np.float32)
        self.next_observations = np.empty_like(self.observations)
        self.actions = np.empty(capacity, dtype=np.int64)
        self.rewards = np.empty(capacity, dtype=np.float32)
        self.terminated = np.empty(capacity, dtype=np.float32)
        self.next_action_masks = np.empty((capacity, action_count), dtype=bool)
        self.position = 0
        self.size = 0

    def add(
        self,
        observation: np.ndarray,
        action: int,
        reward: float,
        next_observation: np.ndarray,
        terminated: bool,
        next_action_mask: np.ndarray,
    ) -> None:
        index = self.position
        self.observations[index] = observation
        self.actions[index] = action
        self.rewards[index] = reward
        self.next_observations[index] = next_observation
        self.terminated[index] = float(terminated)
        self.next_action_masks[index] = next_action_mask
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int, rng: np.random.Generator) -> tuple[np.ndarray, ...]:
        indices = rng.integers(0, self.size, size=batch_size)
        return (
            self.observations[indices],
            self.actions[indices],
            self.rewards[indices],
            self.next_observations[indices],
            self.terminated[indices],
            self.next_action_masks[indices],
        )


class DQNAgent:
    """Shared implementation with a switch for Double-DQN targets."""

    def __init__(
        self,
        observation_size: int,
        action_count: int,
        *,
        config: DQNConfig | None = None,
        double_dqn: bool = False,
        seed: int = 20230722,
        device: str | torch.device = "cpu",
    ) -> None:
        self.config = config or DQNConfig()
        self.double_dqn = double_dqn
        self.seed = seed
        self.observation_size = observation_size
        self.action_count = action_count
        self.device = torch.device(device)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        self.rng = np.random.default_rng(seed)
        self.online = QNetwork(
            observation_size,
            action_count,
            hidden_sizes=self.config.hidden_sizes,
        ).to(self.device)
        self.target = QNetwork(
            observation_size,
            action_count,
            hidden_sizes=self.config.hidden_sizes,
        ).to(self.device)
        self.target.load_state_dict(self.online.state_dict())
        self.target.eval()
        self.optimizer = torch.optim.Adam(self.online.parameters(), lr=self.config.learning_rate)
        self.replay = ReplayBuffer(self.config.replay_capacity, observation_size, action_count)
        self.interaction_steps = 0
        self.optimization_steps = 0

    def epsilon(self) -> float:
        progress = min(self.interaction_steps / self.config.epsilon_decay_steps, 1.0)
        return self.config.epsilon_start + progress * (
            self.config.epsilon_end - self.config.epsilon_start
        )

    def act(self, observation: np.ndarray, action_mask: np.ndarray, *, explore: bool = True) -> int:
        valid_actions = np.flatnonzero(action_mask)
        if len(valid_actions) == 0:
            raise ValueError("at least one action must be valid")
        if explore and self.rng.random() < self.epsilon():
            return int(self.rng.choice(valid_actions))
        with torch.no_grad():
            values = self.online(
                torch.as_tensor(observation, dtype=torch.float32, device=self.device).unsqueeze(0)
            ).squeeze(0)
            mask = torch.as_tensor(action_mask, dtype=torch.bool, device=self.device)
            values = values.masked_fill(~mask, -torch.inf)
            return int(values.argmax().item())

    def observe(
        self,
        observation: np.ndarray,
        action: int,
        reward: float,
        next_observation: np.ndarray,
        terminated: bool,
        next_action_mask: np.ndarray,
    ) -> float | None:
        self.replay.add(
            observation,
            action,
            reward,
            next_observation,
            terminated,
            next_action_mask,
        )
        self.interaction_steps += 1
        if self.replay.size < self.config.learning_starts:
            return None
        loss = self._optimize()
        if self.optimization_steps % self.config.target_update_interval == 0:
            self.target.load_state_dict(self.online.state_dict())
        return loss

    def _optimize(self) -> float:
        batch = self.replay.sample(self.config.batch_size, self.rng)
        observations, actions, rewards, next_observations, terminated, next_masks = (
            torch.as_tensor(value, device=self.device) for value in batch
        )
        observations = observations.float()
        next_observations = next_observations.float()
        actions = actions.long()
        rewards = rewards.float()
        terminated = terminated.float()
        next_masks = next_masks.bool()
        current_values = self.online(observations).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            online_next = self.online(next_observations)
            target_next = self.target(next_observations)
            bootstrap = select_bootstrap_values(
                online_next,
                target_next,
                next_masks,
                double_dqn=self.double_dqn,
            )
            targets = rewards + (1.0 - terminated) * self.config.gamma * bootstrap
        loss = nn.functional.smooth_l1_loss(current_values, targets)
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(self.online.parameters(), self.config.gradient_clip)
        self.optimizer.step()
        self.optimization_steps += 1
        return float(loss.item())

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "observation_size": self.observation_size,
                "action_count": self.action_count,
                "double_dqn": self.double_dqn,
                "seed": self.seed,
                "config": asdict(self.config),
                "state_dict": self.online.state_dict(),
                "interaction_steps": self.interaction_steps,
                "optimization_steps": self.optimization_steps,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path, *, device: str | torch.device = "cpu") -> DQNAgent:
        checkpoint = torch.load(path, map_location=device, weights_only=False)
        config_data = dict(checkpoint["config"])
        config_data["hidden_sizes"] = tuple(config_data["hidden_sizes"])
        agent = cls(
            checkpoint["observation_size"],
            checkpoint["action_count"],
            config=DQNConfig(**config_data),
            double_dqn=checkpoint["double_dqn"],
            seed=checkpoint["seed"],
            device=device,
        )
        agent.online.load_state_dict(checkpoint["state_dict"])
        agent.target.load_state_dict(checkpoint["state_dict"])
        agent.interaction_steps = checkpoint["interaction_steps"]
        agent.optimization_steps = checkpoint["optimization_steps"]
        return agent


def train_agent(
    env: gym.Env,
    *,
    episodes: int,
    config: DQNConfig | None = None,
    double_dqn: bool,
    seed: int,
    device: str | torch.device = "cpu",
) -> tuple[DQNAgent, dict[str, object]]:
    """Train one baseline and return reproducible episode diagnostics."""
    if episodes <= 0:
        raise ValueError("episodes must be positive")
    agent = DQNAgent(
        env.observation_space.shape[0],
        env.action_space.n,
        config=config,
        double_dqn=double_dqn,
        seed=seed,
        device=device,
    )
    returns = []
    fares = []
    fulfilled = []
    losses = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        terminated = False
        episode_return = 0.0
        while not terminated:
            action = agent.act(observation, info["action_mask"])
            next_observation, reward, terminated, truncated, next_info = env.step(action)
            if truncated:
                terminated = True
            loss = agent.observe(
                observation,
                action,
                reward,
                next_observation,
                terminated,
                next_info["action_mask"],
            )
            if loss is not None:
                losses.append(loss)
            observation = next_observation
            info = next_info
            episode_return += reward
        returns.append(episode_return)
        fares.append(float(info["total_fare"]))
        fulfilled.append(int(info["fulfilled_trips"]))
    return agent, {
        "episodes": episodes,
        "seed": seed,
        "double_dqn": double_dqn,
        "interaction_steps": agent.interaction_steps,
        "optimization_steps": agent.optimization_steps,
        "mean_return_last_20": float(np.mean(returns[-20:])),
        "mean_fare_last_20": float(np.mean(fares[-20:])),
        "mean_fulfilled_last_20": float(np.mean(fulfilled[-20:])),
        "mean_loss_last_100": float(np.mean(losses[-100:])) if losses else None,
        "episode_returns": returns,
        "episode_fares": fares,
    }

"""DQN and Double-DQN target semantics."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import torch

from src.rl import DQNStrategy, ObservationEncoder
from src.rl.dqn import DQNAgent, DQNConfig, QNetwork, select_bootstrap_values


def test_double_dqn_uses_online_argmax_and_target_evaluation():
    online = torch.tensor([[10.0, 2.0, 4.0]])
    target = torch.tensor([[1.0, 5.0, 3.0]])
    mask = torch.tensor([[True, True, True]])
    assert select_bootstrap_values(online, target, mask, double_dqn=False).item() == 5.0
    assert select_bootstrap_values(online, target, mask, double_dqn=True).item() == 1.0


def test_bootstrap_masks_invalid_actions():
    online = torch.tensor([[10.0, 2.0, 4.0]])
    target = torch.tensor([[9.0, 5.0, 3.0]])
    mask = torch.tensor([[False, True, True]])
    assert select_bootstrap_values(online, target, mask, double_dqn=False).item() == 5.0
    assert select_bootstrap_values(online, target, mask, double_dqn=True).item() == 3.0


def test_bootstrap_is_zero_when_every_action_is_masked():
    online = torch.tensor([[10.0, 2.0, 4.0]])
    target = torch.tensor([[9.0, 5.0, 3.0]])
    mask = torch.tensor([[False, False, False]])
    assert select_bootstrap_values(online, target, mask, double_dqn=False).item() == 0.0
    assert select_bootstrap_values(online, target, mask, double_dqn=True).item() == 0.0


def test_q_network_has_reproducible_shape():
    torch.manual_seed(7)
    first = QNetwork(6, 3, hidden_sizes=(8,))
    torch.manual_seed(7)
    second = QNetwork(6, 3, hidden_sizes=(8,))
    inputs = torch.ones((2, 6))
    assert first(inputs).shape == (2, 3)
    assert torch.equal(first(inputs), second(inputs))


def test_dqn_strategy_precomputes_valid_top3():
    demand = np.ones((336, 3), dtype=np.float32)
    fare = np.ones_like(demand)
    travel = np.zeros((3, 3), dtype=np.float32)
    encoder = ObservationEncoder(
        demand,
        fare,
        travel,
        candidate_count=3,
        background_driver_count=2,
    )
    agent = DQNAgent(
        encoder.observation_size,
        3,
        config=DQNConfig(
            batch_size=2,
            replay_capacity=4,
            learning_starts=2,
            hidden_sizes=(4,),
        ),
        seed=3,
    )
    for parameter in agent.online.parameters():
        parameter.data.zero_()
    strategy = DQNStrategy(agent, encoder, batch_size=64)
    assert strategy.recommend(datetime(2023, 1, 25), 1) == [1, 2, 3]


def test_dqn_strategy_fills_sparse_candidates_with_unique_zones():
    demand = np.ones((336, 3), dtype=np.float32)
    fare = np.ones_like(demand)
    travel = np.full((3, 3), np.inf, dtype=np.float32)
    np.fill_diagonal(travel, 0.0)
    encoder = ObservationEncoder(
        demand,
        fare,
        travel,
        candidate_count=3,
        background_driver_count=2,
    )
    agent = DQNAgent(
        encoder.observation_size,
        3,
        config=DQNConfig(
            batch_size=2,
            replay_capacity=4,
            learning_starts=2,
            hidden_sizes=(4,),
        ),
        seed=3,
    )
    for parameter in agent.online.parameters():
        parameter.data.zero_()

    strategy = DQNStrategy(agent, encoder, batch_size=64)

    assert strategy.recommend(datetime(2023, 1, 25), 2) == [2, 1, 3]

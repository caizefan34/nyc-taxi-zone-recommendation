"""Gymnasium contract tests for the finite-market RL environment."""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import torch
from gymnasium.utils.env_checker import check_env

from src.eval.rollout_core import MarketCell
from src.rl import RLEnvConfig, TaxiRepositionEnv
from src.rl.dqn import DQNConfig, train_agent

START = datetime(2023, 1, 25)


def _environment() -> TaxiRepositionEnv:
    demand = np.zeros((336, 3), dtype=np.float32)
    fare = np.zeros_like(demand)
    demand[:, :] = [10.0, 2.0, 1.0]
    fare[:, :] = [10.0, 5.0, 1.0]
    travel = np.array([[0.0, 1.0, np.inf], [1.0, 0.0, 1.0], [np.inf, 1.0, 0.0]])
    cell = MarketCell()
    cell.append(dropoff_zone=2, fare=10.0, duration_slots=1)
    return TaxiRepositionEnv(
        market={0: cell},
        demand_features=demand,
        fare_features=fare,
        travel_times=travel,
        start=START,
        end=START + timedelta(minutes=30),
        config=RLEnvConfig(
            candidate_count=3,
            background_driver_count=0,
            demand_supply_ratio=1.0,
            start_location_id=1,
            reward_scale=0.1,
        ),
    )


def test_rl_environment_passes_gymnasium_contract():
    check_env(_environment(), skip_render_check=True)


def test_rl_environment_is_seeded_and_serves_finite_trip_once():
    first = _environment()
    second = _environment()
    observation_a, info_a = first.reset(seed=11)
    observation_b, info_b = second.reset(seed=11)
    assert np.array_equal(observation_a, observation_b)
    assert np.array_equal(info_a["action_mask"], info_b["action_mask"])
    assert info_a["candidate_zones"].tolist() == [1, 2, 0]

    _, reward, terminated, truncated, info = first.step(0)
    assert reward == 1.0
    assert terminated
    assert not truncated
    assert info["pickup_success"]
    assert info["remaining_trip_inventory"] == 0


def test_rl_environment_masks_unreachable_candidate_padding():
    _, info = _environment().reset(seed=3)
    assert info["action_mask"].tolist() == [True, True, False]


def test_invalid_padded_action_waits_without_travel_lookup():
    environment = _environment()
    environment.reset(seed=3)
    environment.inventory.clear()
    environment.travel_times[0, 0] = np.inf

    _, reward, terminated, truncated, info = environment.step(2)

    assert reward == -0.1
    assert terminated
    assert not truncated
    assert info["invalid_action"]
    assert info["relocation_slots"] == 0


def test_seeded_training_is_reproducible():
    config = DQNConfig(
        batch_size=2,
        replay_capacity=8,
        learning_starts=2,
        target_update_interval=2,
        epsilon_decay_steps=4,
        hidden_sizes=(4,),
    )
    first, first_diagnostics = train_agent(
        _environment(),
        episodes=3,
        config=config,
        double_dqn=True,
        seed=17,
    )
    second, second_diagnostics = train_agent(
        _environment(),
        episodes=3,
        config=config,
        double_dqn=True,
        seed=17,
    )

    assert first_diagnostics == second_diagnostics
    for first_parameter, second_parameter in zip(
        first.online.parameters(), second.online.parameters(), strict=True
    ):
        assert torch.equal(first_parameter, second_parameter)

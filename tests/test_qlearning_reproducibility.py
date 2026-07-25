"""Reproducibility checks for simulator-trained Q-learning."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


def _load_module():
    path = Path(__file__).resolve().parents[1] / "src/3_extension_task/extension_5_qlearning.py"
    spec = importlib.util.spec_from_file_location("tested_qlearning", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_agents_with_same_seed_sample_same_transition():
    module = _load_module()
    demand = np.zeros((7, 48, 263))
    fare = np.zeros_like(demand)
    demand[0, 0, 0] = 240.0
    fare[0, 0, 0] = 10.0
    travel = np.zeros((263, 263))
    transition = np.eye(263)
    duration = np.zeros(263)
    first = module.QLearningAgent(demand, fare, travel, transition, duration, seed=7)
    second = module.QLearningAgent(demand, fare, travel, transition, duration, seed=7)
    assert first._next_state(0, 0, 0, 0, 0) == second._next_state(0, 0, 0, 0, 0)


def test_extension_is_explicitly_not_offline_rl():
    module = _load_module()
    assert "not batch/offline RL" in module.__doc__

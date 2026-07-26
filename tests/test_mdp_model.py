"""Tests for the corrected Bellman backup."""

from __future__ import annotations

import numpy as np

from src.mdp.model_based import bellman_backup


def test_bellman_backup_advances_time_after_failed_pickup():
    previous = np.array([[10.0], [20.0]])
    probability = np.zeros((2, 1))
    fare = np.zeros((2, 1))
    transition = np.ones((1, 1))
    duration = np.zeros(1, dtype=int)
    movement = np.zeros((1, 1), dtype=int)
    reachable = np.ones((1, 1), dtype=bool)
    values, _ = bellman_backup(
        previous,
        probability,
        fare,
        transition,
        duration,
        movement,
        reachable,
        gamma=0.5,
    )
    assert values[:, 0].tolist() == [10.0, 5.0]


def test_bellman_backup_policy_depends_on_origin_travel_time():
    previous = np.zeros((2, 2))
    probability = np.array([[1.0, 1.0], [1.0, 1.0]])
    fare = np.array([[5.0, 10.0], [20.0, 1.0]])
    transition = np.eye(2)
    duration = np.zeros(2, dtype=int)
    movement = np.array([[0, 1], [1, 0]])
    reachable = np.ones((2, 2), dtype=bool)
    _, policy = bellman_backup(
        previous,
        probability,
        fare,
        transition,
        duration,
        movement,
        reachable,
        gamma=0.5,
    )
    assert policy[0].tolist() == [0, 0]

from __future__ import annotations

from datetime import datetime
import importlib.util
import math
from pathlib import Path
import unittest


STRATEGY_PATH = (
    Path(__file__).resolve().parents[1]
    / "src/2_recommendation_algorithm/improved_strategy.py"
)


def load_strategy():
    spec = importlib.util.spec_from_file_location("improved_strategy", STRATEGY_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ImprovedStrategyFormulaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy = load_strategy()

    def test_stay_action_has_zero_movement_slots(self):
        origin = 131
        self.assertEqual(self.strategy.movement_slots[origin, origin], 0)

    def test_q1_uses_each_candidates_actual_arrival_state(self):
        strategy = self.strategy
        origin = 131
        state = 0 * strategy.SLOT_COUNT + 16
        q1, arrivals, probabilities = strategy._q1_values(origin, state)

        for destination in (origin, 137, 235):
            move = int(strategy.movement_slots[origin, destination])
            arrival = (state + move) % strategy.WEEK_SLOT_COUNT
            demand = strategy.demand[arrival, destination]
            fare = strategy.mean_fare[arrival, destination]
            probability = demand / (demand + strategy.PICKUP_HALF_SATURATION)
            expected = probability * fare / (move + strategy.LAMBDA)
            self.assertEqual(int(arrivals[destination]), arrival)
            self.assertAlmostEqual(float(probabilities[destination]), probability)
            self.assertAlmostEqual(float(q1[destination]), expected)

    def test_q2_matches_required_success_and_failure_formula(self):
        strategy = self.strategy
        origin = 131
        state = 0 * strategy.SLOT_COUNT + 16
        q1, arrivals, probabilities = strategy._q1_values(origin, state)
        q2 = strategy._two_step_values(origin, state)

        for destination in (origin, 137, 235):
            if not strategy.reachable[origin, destination]:
                self.assertTrue(math.isinf(float(q2[destination])))
                continue
            arrival = int(arrivals[destination])
            failure_state = (arrival + 1) % strategy.WEEK_SLOT_COUNT
            failure_value = strategy.v1[destination, failure_state]
            success_value = strategy.success_future[arrival, destination]
            probability = probabilities[destination]
            expected = q1[destination] + strategy.GAMMA * (
                (1.0 - probability) * failure_value
                + probability * success_value
            )
            self.assertAlmostEqual(float(q2[destination]), float(expected))

    def test_recommend_returns_legal_top3(self):
        result = self.strategy.recommend(datetime(2023, 1, 30, 8, 0), 132)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(set(result)), 3)
        self.assertTrue(all(1 <= zone <= 263 for zone in result))


if __name__ == "__main__":
    unittest.main()

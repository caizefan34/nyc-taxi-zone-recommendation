"""Tests for the LLM mobility agent scaffold (echo mode, no provider needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents import MobilityAgent  # noqa: E402
from src.agents.llm_agent import TOOL_NAMES, _ToolError  # noqa: E402


@pytest.fixture()
def agent():
    return MobilityAgent()


class TestAgentTools:
    def test_tool_names_registered(self, agent):
        assert agent.tool_names() == list(TOOL_NAMES)

    def test_recommend_via_echo_planner(self, agent):
        turn = agent.handle("where should I head next? recommend zone 161")
        assert turn.dispatches[0]["tool"] == "recommend"
        assert turn.dispatches[0]["evaluation_type"] == "simulation"
        assert "recommended_zone" in turn.answer or "Recommendation" in turn.answer
        assert "not production evidence" in turn.answer

    def test_forecast_via_echo_planner(self, agent):
        turn = agent.handle("forecast demand for zone 161")
        assert turn.dispatches[0]["tool"] == "forecast"
        assert turn.dispatches[0]["evaluation_type"] == "historical_replay"
        assert "Historical average" in turn.answer

    def test_simulate_via_echo_planner(self, agent):
        turn = agent.handle("simulate hot_zone with 10 drivers for 1 day")
        assert turn.dispatches[0]["tool"] == "simulate"
        assert turn.dispatches[0]["evaluation_type"] == "simulation"
        assert "Simulation:" in turn.answer
        assert "Simulator only" in turn.answer

    def test_evaluate_via_echo_planner(self, agent):
        turn = agent.handle("evaluate two_step benchmark")
        assert turn.dispatches[0]["tool"] == "evaluate"
        assert turn.dispatches[0]["evaluation_type"] == "offline"
        assert "Not real-world A/B evidence" in turn.answer

    def test_every_tool_output_is_labeled(self, agent):
        for prompt in ["recommend", "forecast", "simulate", "evaluate"]:
            turn = agent.handle(prompt)
            assert "evaluation_type" in turn.dispatches[0]
            assert turn.answer  # never an empty answer


class TestAgentPlanner:
    def test_custom_planner_is_used(self):
        calls = []

        def planner(prompt, tools):
            calls.append(prompt)
            return {"tool": "forecast", "arguments": {"zone_id": 132}}

        agent = MobilityAgent(planner=planner)
        turn = agent.handle("anything")
        assert calls == ["anything"]
        assert turn.dispatches[0]["tool"] == "forecast"

    def test_unknown_tool_raises(self):
        def planner(prompt, tools):
            return {"tool": "nope", "arguments": {}}

        agent = MobilityAgent(planner=planner)
        with pytest.raises(_ToolError):
            agent.handle("hi")

    def test_unknown_policy_raises(self):
        def planner(prompt, tools):
            return {"tool": "recommend", "arguments": {"model_name": "nope"}}

        agent = MobilityAgent(planner=planner)
        with pytest.raises(_ToolError):
            agent.handle("hi")

    def test_invalid_evaluation_type_raises(self):
        def planner(prompt, tools):
            return {"tool": "evaluate", "arguments": {"evaluation_type": "bogus"}}

        agent = MobilityAgent(planner=planner)
        with pytest.raises(_ToolError):
            agent.handle("hi")

    def test_echo_planner_defaults_to_recommend(self, agent):
        turn = agent.handle("hello there")
        assert turn.dispatches[0]["tool"] == "recommend"

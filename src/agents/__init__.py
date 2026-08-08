"""LLM mobility agent scaffold.

A tool-using conversational interface over the decision platform. The agent
does NOT make decisions — the platform's policies do. The agent renders,
explains, and answers operational questions by calling platform tools
(recommend / forecast / simulate / evaluate).

All outputs are labeled by evaluation type. Nothing here is production evidence.
"""

from src.agents.llm_agent import MobilityAgent, ToolResult
from src.agents.planners import AnthropicPlanner, OpenAICompatiblePlanner, planner_from_env

__all__ = ["MobilityAgent", "ToolResult", "AnthropicPlanner", "OpenAICompatiblePlanner", "planner_from_env"]

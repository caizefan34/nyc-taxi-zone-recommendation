"""Compatibility wrapper for the model-based MDP solver."""

from src.mdp.model_based import MDPValueIteration, recommend

__all__ = ["MDPValueIteration", "recommend"]

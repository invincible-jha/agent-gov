"""Framework adapters for agent_gov.

Each adapter enforces governance policy and records audit decisions for a
specific agent framework without requiring the framework to be installed.
"""
from __future__ import annotations

from agent_gov.adapters.anthropic_sdk import AnthropicGovernance
from agent_gov.adapters.crewai import CrewAIGovernance
from agent_gov.adapters.langchain import LangChainGovernance
from agent_gov.adapters.microsoft_agents import MicrosoftGovernance
from agent_gov.adapters.openai_agents import OpenAIGovernance

__all__ = [
    "AnthropicGovernance",
    "CrewAIGovernance",
    "LangChainGovernance",
    "MicrosoftGovernance",
    "OpenAIGovernance",
]

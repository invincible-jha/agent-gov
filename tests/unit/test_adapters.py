"""Unit tests for agent_gov framework adapters."""
from __future__ import annotations

import pytest

from agent_gov.adapters import (
    AnthropicGovernance,
    CrewAIGovernance,
    LangChainGovernance,
    MicrosoftGovernance,
    OpenAIGovernance,
)


# ---------------------------------------------------------------------------
# LangChainGovernance
# ---------------------------------------------------------------------------


class TestLangChainGovernance:
    def test_construction_no_args(self) -> None:
        adapter = LangChainGovernance()
        assert adapter.policy_engine is None
        assert adapter._audit_log == []

    def test_construction_with_engine(self) -> None:
        sentinel = object()
        adapter = LangChainGovernance(policy_engine=sentinel)
        assert adapter.policy_engine is sentinel

    def test_check_prompt_returns_dict(self) -> None:
        adapter = LangChainGovernance()
        result = adapter.check_prompt("Is this safe?")
        assert isinstance(result, dict)

    def test_check_prompt_allowed_key(self) -> None:
        adapter = LangChainGovernance()
        result = adapter.check_prompt("hello")
        assert "allowed" in result
        assert result["allowed"] is True
        assert "reason" in result

    def test_check_output_returns_dict(self) -> None:
        adapter = LangChainGovernance()
        result = adapter.check_output("The answer is 42.")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_tool_call_returns_dict(self) -> None:
        adapter = LangChainGovernance()
        result = adapter.check_tool_call("web_search", {"query": "python"})
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_get_audit_log_returns_list(self) -> None:
        adapter = LangChainGovernance()
        adapter.check_prompt("hello")
        log = adapter.get_audit_log()
        assert isinstance(log, list)
        assert len(log) == 1

    def test_audit_log_grows_with_checks(self) -> None:
        adapter = LangChainGovernance()
        adapter.check_prompt("p")
        adapter.check_output("o")
        adapter.check_tool_call("t", {})
        assert len(adapter.get_audit_log()) == 3

    def test_audit_log_contains_timestamps(self) -> None:
        adapter = LangChainGovernance()
        adapter.check_prompt("test")
        log = adapter.get_audit_log()
        assert "timestamp" in log[0]

    def test_get_audit_log_returns_copy(self) -> None:
        adapter = LangChainGovernance()
        adapter.check_prompt("p")
        log = adapter.get_audit_log()
        log.clear()
        assert len(adapter._audit_log) == 1


# ---------------------------------------------------------------------------
# CrewAIGovernance
# ---------------------------------------------------------------------------


class TestCrewAIGovernance:
    def test_construction_no_args(self) -> None:
        adapter = CrewAIGovernance()
        assert adapter.policy_engine is None
        assert adapter._audit_log == []

    def test_construction_with_engine(self) -> None:
        sentinel = object()
        adapter = CrewAIGovernance(policy_engine=sentinel)
        assert adapter.policy_engine is sentinel

    def test_check_task_returns_dict(self) -> None:
        adapter = CrewAIGovernance()
        result = adapter.check_task("analyse_data", {"data": "..."})
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_agent_action_returns_dict(self) -> None:
        adapter = CrewAIGovernance()
        result = adapter.check_agent_action("researcher", "web_search")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_delegation_returns_dict(self) -> None:
        adapter = CrewAIGovernance()
        result = adapter.check_delegation("manager", "worker")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_audit_log_grows_with_each_check(self) -> None:
        adapter = CrewAIGovernance()
        adapter.check_task("t", {})
        adapter.check_agent_action("a", "act")
        adapter.check_delegation("f", "to")
        assert len(adapter.get_audit_log()) == 3

    def test_audit_log_event_types(self) -> None:
        adapter = CrewAIGovernance()
        adapter.check_task("t", {})
        log = adapter.get_audit_log()
        assert log[0]["event_type"] == "check_task"


# ---------------------------------------------------------------------------
# OpenAIGovernance
# ---------------------------------------------------------------------------


class TestOpenAIGovernance:
    def test_construction_no_args(self) -> None:
        adapter = OpenAIGovernance()
        assert adapter.policy_engine is None
        assert adapter._audit_log == []

    def test_construction_with_engine(self) -> None:
        sentinel = object()
        adapter = OpenAIGovernance(policy_engine=sentinel)
        assert adapter.policy_engine is sentinel

    def test_check_message_returns_dict(self) -> None:
        adapter = OpenAIGovernance()
        result = adapter.check_message("user", "Tell me a joke.")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_tool_use_returns_dict(self) -> None:
        adapter = OpenAIGovernance()
        result = adapter.check_tool_use("calculator", {"expr": "2+2"})
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_handoff_returns_dict(self) -> None:
        adapter = OpenAIGovernance()
        result = adapter.check_handoff("TriageAgent", "SpecialistAgent")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_audit_log_grows_with_each_check(self) -> None:
        adapter = OpenAIGovernance()
        adapter.check_message("user", "hello")
        adapter.check_tool_use("search", {})
        adapter.check_handoff("A", "B")
        assert len(adapter.get_audit_log()) == 3

    def test_check_handoff_records_agents(self) -> None:
        adapter = OpenAIGovernance()
        adapter.check_handoff("Alpha", "Beta")
        log = adapter.get_audit_log()
        assert log[0]["from_agent"] == "Alpha"
        assert log[0]["to_agent"] == "Beta"


# ---------------------------------------------------------------------------
# AnthropicGovernance
# ---------------------------------------------------------------------------


class TestAnthropicGovernance:
    def test_construction_no_args(self) -> None:
        adapter = AnthropicGovernance()
        assert adapter.policy_engine is None
        assert adapter._audit_log == []

    def test_construction_with_engine(self) -> None:
        sentinel = object()
        adapter = AnthropicGovernance(policy_engine=sentinel)
        assert adapter.policy_engine is sentinel

    def test_check_message_returns_dict(self) -> None:
        adapter = AnthropicGovernance()
        result = adapter.check_message("user", "Hello Claude.")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_tool_use_returns_dict(self) -> None:
        adapter = AnthropicGovernance()
        result = adapter.check_tool_use("bash", {"command": "ls"})
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_content_returns_dict(self) -> None:
        adapter = AnthropicGovernance()
        result = adapter.check_content("text", "Here is an answer.")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_audit_log_grows_with_each_check(self) -> None:
        adapter = AnthropicGovernance()
        adapter.check_message("user", "m")
        adapter.check_tool_use("t", {})
        adapter.check_content("text", "c")
        assert len(adapter.get_audit_log()) == 3

    def test_check_content_records_length(self) -> None:
        adapter = AnthropicGovernance()
        adapter.check_content("text", "hello world")
        log = adapter.get_audit_log()
        assert log[0]["content_length"] == len("hello world")


# ---------------------------------------------------------------------------
# MicrosoftGovernance
# ---------------------------------------------------------------------------


class TestMicrosoftGovernance:
    def test_construction_no_args(self) -> None:
        adapter = MicrosoftGovernance()
        assert adapter.policy_engine is None
        assert adapter._audit_log == []

    def test_construction_with_engine(self) -> None:
        sentinel = object()
        adapter = MicrosoftGovernance(policy_engine=sentinel)
        assert adapter.policy_engine is sentinel

    def test_check_activity_returns_dict(self) -> None:
        adapter = MicrosoftGovernance()
        result = adapter.check_activity("message", {"text": "Hi"})
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_dialog_returns_dict(self) -> None:
        adapter = MicrosoftGovernance()
        result = adapter.check_dialog("main_dialog", "prompt_name")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_check_turn_returns_dict(self) -> None:
        adapter = MicrosoftGovernance()
        result = adapter.check_turn("turn-001", "Hello, how can I help?")
        assert isinstance(result, dict)
        assert result["allowed"] is True

    def test_audit_log_grows_with_each_check(self) -> None:
        adapter = MicrosoftGovernance()
        adapter.check_activity("message", {})
        adapter.check_dialog("d", "s")
        adapter.check_turn("t", "content")
        assert len(adapter.get_audit_log()) == 3

    def test_check_turn_records_content_length(self) -> None:
        adapter = MicrosoftGovernance()
        adapter.check_turn("turn-1", "hello")
        log = adapter.get_audit_log()
        assert log[0]["content_length"] == len("hello")

    def test_get_audit_log_returns_copy(self) -> None:
        adapter = MicrosoftGovernance()
        adapter.check_activity("msg", {})
        log = adapter.get_audit_log()
        log.clear()
        assert len(adapter._audit_log) == 1

    def test_all_classes_importable_from_init(self) -> None:
        from agent_gov.adapters import (
            AnthropicGovernance,
            CrewAIGovernance,
            LangChainGovernance,
            MicrosoftGovernance,
            OpenAIGovernance,
        )
        assert LangChainGovernance is not None
        assert CrewAIGovernance is not None
        assert OpenAIGovernance is not None
        assert AnthropicGovernance is not None
        assert MicrosoftGovernance is not None

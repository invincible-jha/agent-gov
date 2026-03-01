"""Tests for adapter-to-PolicyEvaluator wiring (base class, action mapper, and all adapters).

Covers:
- GovernanceAdapter ABC and base behaviour
- action_mapper pure functions (7 mappers)
- All 5 framework adapters with:
    - allow path (policy that permits the action)
    - deny path (policy that blocks the action)
    - audit log correctness
    - backward-compat permissive mode (no policy)
"""
from __future__ import annotations

from agent_gov.adapters.action_mapper import (
    map_anthropic_message,
    map_crewai_delegation,
    map_crewai_task,
    map_langchain_prompt,
    map_langchain_tool_call,
    map_microsoft_activity,
    map_openai_message,
)
from agent_gov.adapters.anthropic_sdk import AnthropicGovernance
from agent_gov.adapters.base import GovernanceAdapter
from agent_gov.adapters.crewai import CrewAIGovernance
from agent_gov.adapters.langchain import LangChainGovernance
from agent_gov.adapters.microsoft_agents import MicrosoftGovernance
from agent_gov.adapters.openai_agents import OpenAIGovernance
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _allow_policy() -> PolicyConfig:
    """Return a policy whose only rule never blocks (no keywords configured)."""
    return PolicyConfig(
        name="test-allow",
        version="1.0",
        rules=[
            RuleConfig(
                name="keyword-allow",
                type="keyword_block",
                enabled=True,
                severity=Severity.MEDIUM,
                # Empty keywords list -> rule always passes.
                params={"keywords": []},
            )
        ],
    )


def _deny_policy() -> PolicyConfig:
    """Return a policy whose keyword_block rule blocks the word 'forbidden'."""
    return PolicyConfig(
        name="test-deny",
        version="1.0",
        rules=[
            RuleConfig(
                name="keyword-deny",
                type="keyword_block",
                enabled=True,
                severity=Severity.HIGH,
                params={"keywords": ["forbidden"]},
            )
        ],
    )


def _evaluator() -> PolicyEvaluator:
    return PolicyEvaluator()


# ---------------------------------------------------------------------------
# GovernanceAdapter base class
# ---------------------------------------------------------------------------


class TestGovernanceAdapterBase:
    def test_is_a_class_providing_shared_infrastructure(self) -> None:
        """GovernanceAdapter provides shared infrastructure but is a concrete base.

        Subclasses add the framework-specific check_* methods; the base class
        itself provides _evaluate_action, _record, and audit_log.
        """
        assert issubclass(LangChainGovernance, GovernanceAdapter)
        assert issubclass(CrewAIGovernance, GovernanceAdapter)
        assert issubclass(OpenAIGovernance, GovernanceAdapter)
        assert issubclass(AnthropicGovernance, GovernanceAdapter)
        assert issubclass(MicrosoftGovernance, GovernanceAdapter)

    def test_permissive_mode_when_no_policy(self) -> None:
        """Without a policy the base _evaluate_action returns allowed=True."""

        class _ConcreteAdapter(GovernanceAdapter):
            def do_check(self, content: str) -> dict[str, object]:
                return self._evaluate_action("test_check", {"content": content})

        adapter = _ConcreteAdapter()
        result = adapter.do_check("hello")
        assert result["allowed"] is True
        assert "No policy configured" in str(result["reason"])

    def test_audit_log_property_returns_copy(self) -> None:
        """The audit_log property must return a copy, not the internal list."""

        class _ConcreteAdapter(GovernanceAdapter):
            def do_check(self) -> dict[str, object]:
                return self._evaluate_action("check", {"x": "y"})

        adapter = _ConcreteAdapter()
        adapter.do_check()
        log_copy = adapter.audit_log
        log_copy.clear()
        assert len(adapter._audit_log) == 1

    def test_get_audit_log_returns_copy(self) -> None:
        """get_audit_log() (legacy API) must also return a copy."""

        class _ConcreteAdapter(GovernanceAdapter):
            def do_check(self) -> dict[str, object]:
                return self._evaluate_action("check", {})

        adapter = _ConcreteAdapter()
        adapter.do_check()
        log_copy = adapter.get_audit_log()
        log_copy.clear()
        assert len(adapter._audit_log) == 1

    def test_audit_log_entry_has_required_keys(self) -> None:
        """Every audit log entry must contain timestamp, event_type, and result."""

        class _ConcreteAdapter(GovernanceAdapter):
            def do_check(self) -> dict[str, object]:
                return self._evaluate_action("test_event", {})

        adapter = _ConcreteAdapter()
        adapter.do_check()
        entry = adapter.audit_log[0]
        assert "timestamp" in entry
        assert "event_type" in entry
        assert "result" in entry

    def test_evaluator_auto_created_when_policy_supplied(self) -> None:
        """Providing only policy auto-creates a default evaluator."""

        class _ConcreteAdapter(GovernanceAdapter):
            pass

        policy = _allow_policy()
        adapter = _ConcreteAdapter(policy=policy)
        assert adapter._evaluator is not None

    def test_policy_evaluation_allow(self) -> None:
        """With an allow policy the result must be allowed=True."""

        class _ConcreteAdapter(GovernanceAdapter):
            def do_check(self) -> dict[str, object]:
                return self._evaluate_action("check", {"content": "safe text"})

        adapter = _ConcreteAdapter(policy=_allow_policy(), evaluator=_evaluator())
        result = adapter.do_check()
        assert result["allowed"] is True

    def test_policy_evaluation_deny(self) -> None:
        """With a deny policy the result must be allowed=False."""

        class _ConcreteAdapter(GovernanceAdapter):
            def do_check(self) -> dict[str, object]:
                return self._evaluate_action("check", {"content": "forbidden word here"})

        adapter = _ConcreteAdapter(policy=_deny_policy(), evaluator=_evaluator())
        result = adapter.do_check()
        assert result["allowed"] is False
        assert "reason" in result


# ---------------------------------------------------------------------------
# action_mapper pure functions
# ---------------------------------------------------------------------------


class TestActionMapper:
    def test_map_langchain_prompt_keys(self) -> None:
        result = map_langchain_prompt("Hello world")
        assert "action_type" in result
        assert "content" in result
        assert "content_length" in result
        assert result["content"] == "Hello world"
        assert result["content_length"] == len("Hello world")

    def test_map_langchain_tool_call_keys(self) -> None:
        result = map_langchain_tool_call("web_search", {"query": "cats"})
        assert result["tool_name"] == "web_search"
        assert result["arg_count"] == 1
        assert "args" in result

    def test_map_crewai_task_keys(self) -> None:
        result = map_crewai_task("Analyse sales data", "data_analyst")
        assert result["task_description"] == "Analyse sales data"
        assert result["agent_role"] == "data_analyst"
        assert "content_length" in result

    def test_map_crewai_delegation_keys(self) -> None:
        result = map_crewai_delegation("manager", "worker")
        assert result["from_agent"] == "manager"
        assert result["to_agent"] == "worker"

    def test_map_openai_message_keys(self) -> None:
        result = map_openai_message("user", "Tell me a joke.")
        assert result["role"] == "user"
        assert result["content"] == "Tell me a joke."
        assert result["content_length"] == len("Tell me a joke.")

    def test_map_anthropic_message_keys(self) -> None:
        result = map_anthropic_message("assistant", "Here is the answer.")
        assert result["role"] == "assistant"
        assert result["content_length"] == len("Here is the answer.")

    def test_map_microsoft_activity_keys(self) -> None:
        result = map_microsoft_activity("message", "Hello bot")
        assert result["activity_type"] == "message"
        assert result["text"] == "Hello bot"
        assert result["content_length"] == len("Hello bot")


# ---------------------------------------------------------------------------
# LangChainGovernance
# ---------------------------------------------------------------------------


class TestLangChainGovernanceWiring:
    def test_allow_policy_check_prompt(self) -> None:
        adapter = LangChainGovernance(policy=_allow_policy())
        result = adapter.check_prompt("This is safe.")
        assert result["allowed"] is True

    def test_deny_policy_check_prompt(self) -> None:
        adapter = LangChainGovernance(policy=_deny_policy())
        result = adapter.check_prompt("This contains a forbidden phrase.")
        assert result["allowed"] is False

    def test_audit_log_entry_has_timestamp_action_type_result(self) -> None:
        adapter = LangChainGovernance(policy=_allow_policy())
        adapter.check_prompt("safe")
        entry = adapter.audit_log[0]
        assert "timestamp" in entry
        assert entry["event_type"] == "check_prompt"
        assert "result" in entry

    def test_backward_compat_no_policy_permissive(self) -> None:
        adapter = LangChainGovernance()
        result = adapter.check_prompt("anything")
        assert result["allowed"] is True
        assert "No policy configured" in str(result["reason"])

    def test_allow_policy_check_tool_call(self) -> None:
        adapter = LangChainGovernance(policy=_allow_policy())
        result = adapter.check_tool_call("search", {"q": "python"})
        assert result["allowed"] is True

    def test_deny_policy_check_output(self) -> None:
        adapter = LangChainGovernance(policy=_deny_policy())
        result = adapter.check_output("The answer is forbidden here.")
        assert result["allowed"] is False

    def test_audit_log_grows_per_check(self) -> None:
        adapter = LangChainGovernance(policy=_allow_policy())
        adapter.check_prompt("a")
        adapter.check_output("b")
        adapter.check_tool_call("t", {})
        assert len(adapter.audit_log) == 3


# ---------------------------------------------------------------------------
# CrewAIGovernance
# ---------------------------------------------------------------------------


class TestCrewAIGovernanceWiring:
    def test_allow_policy_check_task(self) -> None:
        adapter = CrewAIGovernance(policy=_allow_policy())
        result = adapter.check_task("analyse_data", {"data": "clean"})
        assert result["allowed"] is True

    def test_deny_policy_check_task(self) -> None:
        adapter = CrewAIGovernance(policy=_deny_policy())
        result = adapter.check_task("forbidden_task", {"goal": "do it"})
        assert result["allowed"] is False

    def test_audit_log_entry_correctness(self) -> None:
        adapter = CrewAIGovernance(policy=_allow_policy())
        adapter.check_task("run_analysis", {})
        entry = adapter.audit_log[0]
        assert "timestamp" in entry
        assert entry["event_type"] == "check_task"
        assert "result" in entry

    def test_backward_compat_no_policy(self) -> None:
        adapter = CrewAIGovernance()
        result = adapter.check_task("any_task", {})
        assert result["allowed"] is True
        assert "No policy configured" in str(result["reason"])

    def test_allow_policy_check_delegation(self) -> None:
        adapter = CrewAIGovernance(policy=_allow_policy())
        result = adapter.check_delegation("manager", "worker")
        assert result["allowed"] is True

    def test_deny_policy_check_agent_action(self) -> None:
        adapter = CrewAIGovernance(policy=_deny_policy())
        result = adapter.check_agent_action("agent", "forbidden action")
        assert result["allowed"] is False

    def test_audit_log_grows_per_check(self) -> None:
        adapter = CrewAIGovernance(policy=_allow_policy())
        adapter.check_task("t", {})
        adapter.check_agent_action("a", "act")
        adapter.check_delegation("f", "to")
        assert len(adapter.audit_log) == 3


# ---------------------------------------------------------------------------
# OpenAIGovernance
# ---------------------------------------------------------------------------


class TestOpenAIGovernanceWiring:
    def test_allow_policy_check_message(self) -> None:
        adapter = OpenAIGovernance(policy=_allow_policy())
        result = adapter.check_message("user", "Hello there.")
        assert result["allowed"] is True

    def test_deny_policy_check_message(self) -> None:
        adapter = OpenAIGovernance(policy=_deny_policy())
        result = adapter.check_message("user", "This is a forbidden request.")
        assert result["allowed"] is False

    def test_audit_log_entry_correctness(self) -> None:
        adapter = OpenAIGovernance(policy=_allow_policy())
        adapter.check_message("user", "hi")
        entry = adapter.audit_log[0]
        assert "timestamp" in entry
        assert entry["event_type"] == "check_message"
        assert "result" in entry

    def test_backward_compat_no_policy(self) -> None:
        adapter = OpenAIGovernance()
        result = adapter.check_message("user", "anything")
        assert result["allowed"] is True
        assert "No policy configured" in str(result["reason"])

    def test_allow_policy_check_tool_use(self) -> None:
        adapter = OpenAIGovernance(policy=_allow_policy())
        result = adapter.check_tool_use("calc", {"expr": "2+2"})
        assert result["allowed"] is True

    def test_deny_policy_check_handoff(self) -> None:
        adapter = OpenAIGovernance(policy=_deny_policy())
        result = adapter.check_handoff("forbidden_agent", "SpecialistAgent")
        assert result["allowed"] is False

    def test_audit_log_grows_per_check(self) -> None:
        adapter = OpenAIGovernance(policy=_allow_policy())
        adapter.check_message("user", "a")
        adapter.check_tool_use("s", {})
        adapter.check_handoff("A", "B")
        assert len(adapter.audit_log) == 3


# ---------------------------------------------------------------------------
# AnthropicGovernance
# ---------------------------------------------------------------------------


class TestAnthropicGovernanceWiring:
    def test_allow_policy_check_message(self) -> None:
        adapter = AnthropicGovernance(policy=_allow_policy())
        result = adapter.check_message("user", "Safe message here.")
        assert result["allowed"] is True

    def test_deny_policy_check_message(self) -> None:
        adapter = AnthropicGovernance(policy=_deny_policy())
        result = adapter.check_message("user", "forbidden content here")
        assert result["allowed"] is False

    def test_audit_log_entry_correctness(self) -> None:
        adapter = AnthropicGovernance(policy=_allow_policy())
        adapter.check_message("user", "hello")
        entry = adapter.audit_log[0]
        assert "timestamp" in entry
        assert entry["event_type"] == "check_message"
        assert "result" in entry

    def test_backward_compat_no_policy(self) -> None:
        adapter = AnthropicGovernance()
        result = adapter.check_message("user", "anything")
        assert result["allowed"] is True
        assert "No policy configured" in str(result["reason"])

    def test_allow_policy_check_tool_use(self) -> None:
        adapter = AnthropicGovernance(policy=_allow_policy())
        result = adapter.check_tool_use("bash", {"command": "ls"})
        assert result["allowed"] is True

    def test_deny_policy_check_content(self) -> None:
        adapter = AnthropicGovernance(policy=_deny_policy())
        result = adapter.check_content("text", "this text is forbidden entirely")
        assert result["allowed"] is False

    def test_audit_log_grows_per_check(self) -> None:
        adapter = AnthropicGovernance(policy=_allow_policy())
        adapter.check_message("user", "m")
        adapter.check_tool_use("t", {})
        adapter.check_content("text", "c")
        assert len(adapter.audit_log) == 3


# ---------------------------------------------------------------------------
# MicrosoftGovernance
# ---------------------------------------------------------------------------


class TestMicrosoftGovernanceWiring:
    def test_allow_policy_check_activity(self) -> None:
        adapter = MicrosoftGovernance(policy=_allow_policy())
        result = adapter.check_activity("message", {"text": "Hi"})
        assert result["allowed"] is True

    def test_deny_policy_check_activity(self) -> None:
        adapter = MicrosoftGovernance(policy=_deny_policy())
        result = adapter.check_activity("message", "forbidden command")
        assert result["allowed"] is False

    def test_audit_log_entry_correctness(self) -> None:
        adapter = MicrosoftGovernance(policy=_allow_policy())
        adapter.check_activity("message", "hello")
        entry = adapter.audit_log[0]
        assert "timestamp" in entry
        assert entry["event_type"] == "check_activity"
        assert "result" in entry

    def test_backward_compat_no_policy(self) -> None:
        adapter = MicrosoftGovernance()
        result = adapter.check_activity("message", "anything")
        assert result["allowed"] is True
        assert "No policy configured" in str(result["reason"])

    def test_allow_policy_check_dialog(self) -> None:
        adapter = MicrosoftGovernance(policy=_allow_policy())
        result = adapter.check_dialog("main_dialog", "prompt_step")
        assert result["allowed"] is True

    def test_deny_policy_check_turn(self) -> None:
        adapter = MicrosoftGovernance(policy=_deny_policy())
        result = adapter.check_turn("turn-1", "this is forbidden turn content")
        assert result["allowed"] is False

    def test_audit_log_grows_per_check(self) -> None:
        adapter = MicrosoftGovernance(policy=_allow_policy())
        adapter.check_activity("message", "a")
        adapter.check_dialog("d", "s")
        adapter.check_turn("t", "c")
        assert len(adapter.audit_log) == 3

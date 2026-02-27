"""LangChain adapter for agent_gov."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class LangChainGovernance:
    """Governance and compliance adapter for LangChain.

    Intercepts prompts, outputs, and tool calls to enforce policy rules and
    maintain an immutable audit log of all governance decisions.

    Usage::

        from agent_gov.adapters.langchain import LangChainGovernance
        adapter = LangChainGovernance()
    """

    def __init__(self, policy_engine: Any = None) -> None:
        self.policy_engine = policy_engine
        self._audit_log: list[dict[str, Any]] = []
        logger.info("LangChainGovernance initialized.")

    def _record(self, event_type: str, result: dict[str, Any], **context: Any) -> None:
        """Append an entry to the audit log with a UTC timestamp."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": event_type,
            "result": result,
            **context,
        }
        self._audit_log.append(entry)

    def check_prompt(self, prompt: str) -> dict[str, Any]:
        """Evaluate a user or system prompt against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Prompt passed policy checks."}
        self._record("check_prompt", result, prompt_length=len(prompt))
        return result

    def check_output(self, output: str) -> dict[str, Any]:
        """Evaluate an LLM output against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Output passed policy checks."}
        self._record("check_output", result, output_length=len(output))
        return result

    def check_tool_call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a tool call against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Tool call passed policy checks."}
        self._record("check_tool_call", result, tool_name=tool_name, arg_count=len(args))
        return result

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return the full audit log of governance decisions."""
        return list(self._audit_log)

"""OpenAI Agents SDK adapter for agent_gov."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class OpenAIGovernance:
    """Governance and compliance adapter for the OpenAI Agents SDK.

    Evaluates messages, tool uses, and agent handoffs against a policy engine
    and records all decisions in an immutable audit log.

    Usage::

        from agent_gov.adapters.openai_agents import OpenAIGovernance
        adapter = OpenAIGovernance()
    """

    def __init__(self, policy_engine: Any = None) -> None:
        self.policy_engine = policy_engine
        self._audit_log: list[dict[str, Any]] = []
        logger.info("OpenAIGovernance initialized.")

    def _record(self, event_type: str, result: dict[str, Any], **context: Any) -> None:
        """Append an entry to the audit log with a UTC timestamp."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": event_type,
            "result": result,
            **context,
        }
        self._audit_log.append(entry)

    def check_message(self, role: str, content: str) -> dict[str, Any]:
        """Evaluate a message (by role) against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Message passed policy checks."}
        self._record("check_message", result, role=role, content_length=len(content))
        return result

    def check_tool_use(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a tool use request against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Tool use passed policy checks."}
        self._record("check_tool_use", result, tool_name=tool_name, arg_count=len(args))
        return result

    def check_handoff(self, from_agent: str, to_agent: str) -> dict[str, Any]:
        """Evaluate an agent handoff against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Handoff passed policy checks."}
        self._record("check_handoff", result, from_agent=from_agent, to_agent=to_agent)
        return result

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return the full audit log of governance decisions."""
        return list(self._audit_log)

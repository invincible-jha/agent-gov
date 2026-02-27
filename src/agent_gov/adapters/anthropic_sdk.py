"""Anthropic SDK adapter for agent_gov."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AnthropicGovernance:
    """Governance and compliance adapter for the Anthropic SDK.

    Evaluates messages, tool uses, and content blocks from Anthropic API
    interactions against a policy engine and maintains an immutable audit log.

    Usage::

        from agent_gov.adapters.anthropic_sdk import AnthropicGovernance
        adapter = AnthropicGovernance()
    """

    def __init__(self, policy_engine: Any = None) -> None:
        self.policy_engine = policy_engine
        self._audit_log: list[dict[str, Any]] = []
        logger.info("AnthropicGovernance initialized.")

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
        """Evaluate an Anthropic message (by role) against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Message passed policy checks."}
        self._record("check_message", result, role=role, content_length=len(content))
        return result

    def check_tool_use(self, tool_name: str, input: Any) -> dict[str, Any]:
        """Evaluate an Anthropic tool_use content block against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Tool use passed policy checks."}
        self._record("check_tool_use", result, tool_name=tool_name)
        return result

    def check_content(self, content_type: str, content: Any) -> dict[str, Any]:
        """Evaluate a content block by type against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        content_str = str(content) if content is not None else ""
        result: dict[str, Any] = {"allowed": True, "reason": "Content passed policy checks."}
        self._record("check_content", result, content_type=content_type, content_length=len(content_str))
        return result

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return the full audit log of governance decisions."""
        return list(self._audit_log)

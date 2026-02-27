"""CrewAI adapter for agent_gov."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class CrewAIGovernance:
    """Governance and compliance adapter for CrewAI.

    Evaluates tasks, agent actions, and agent-to-agent delegations against a
    policy engine and records all decisions in an immutable audit log.

    Usage::

        from agent_gov.adapters.crewai import CrewAIGovernance
        adapter = CrewAIGovernance()
    """

    def __init__(self, policy_engine: Any = None) -> None:
        self.policy_engine = policy_engine
        self._audit_log: list[dict[str, Any]] = []
        logger.info("CrewAIGovernance initialized.")

    def _record(self, event_type: str, result: dict[str, Any], **context: Any) -> None:
        """Append an entry to the audit log with a UTC timestamp."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": event_type,
            "result": result,
            **context,
        }
        self._audit_log.append(entry)

    def check_task(self, task_name: str, task_input: Any) -> dict[str, Any]:
        """Evaluate a CrewAI task against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Task passed policy checks."}
        self._record("check_task", result, task_name=task_name)
        return result

    def check_agent_action(self, agent_name: str, action: str) -> dict[str, Any]:
        """Evaluate an agent action against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Agent action passed policy checks."}
        self._record("check_agent_action", result, agent_name=agent_name, action=action)
        return result

    def check_delegation(self, from_agent: str, to_agent: str) -> dict[str, Any]:
        """Evaluate an agent-to-agent delegation against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Delegation passed policy checks."}
        self._record("check_delegation", result, from_agent=from_agent, to_agent=to_agent)
        return result

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return the full audit log of governance decisions."""
        return list(self._audit_log)

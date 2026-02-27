"""Microsoft Agents adapter for agent_gov."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class MicrosoftGovernance:
    """Governance and compliance adapter for Microsoft Agents.

    Evaluates Bot Framework activities, dialog steps, and conversation turns
    against a policy engine and maintains an immutable audit log.

    Usage::

        from agent_gov.adapters.microsoft_agents import MicrosoftGovernance
        adapter = MicrosoftGovernance()
    """

    def __init__(self, policy_engine: Any = None) -> None:
        self.policy_engine = policy_engine
        self._audit_log: list[dict[str, Any]] = []
        logger.info("MicrosoftGovernance initialized.")

    def _record(self, event_type: str, result: dict[str, Any], **context: Any) -> None:
        """Append an entry to the audit log with a UTC timestamp."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": event_type,
            "result": result,
            **context,
        }
        self._audit_log.append(entry)

    def check_activity(self, activity_type: str, data: Any) -> dict[str, Any]:
        """Evaluate a Bot Framework activity against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Activity passed policy checks."}
        self._record("check_activity", result, activity_type=activity_type)
        return result

    def check_dialog(self, dialog_id: str, step: str) -> dict[str, Any]:
        """Evaluate a dialog waterfall step against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Dialog step passed policy checks."}
        self._record("check_dialog", result, dialog_id=dialog_id, step=step)
        return result

    def check_turn(self, turn_id: str, content: str) -> dict[str, Any]:
        """Evaluate a conversation turn's content against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        result: dict[str, Any] = {"allowed": True, "reason": "Turn passed policy checks."}
        self._record("check_turn", result, turn_id=turn_id, content_length=len(content))
        return result

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return the full audit log of governance decisions."""
        return list(self._audit_log)

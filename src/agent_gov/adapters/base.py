"""Abstract base class for all agent_gov framework adapters.

Provides shared audit logging, policy evaluation dispatch, and permissive
fallback behaviour when no policy is configured.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class GovernanceAdapter:
    """Base class for framework-specific governance adapters.

    Subclasses inherit audit logging and policy evaluation.  When no
    *policy* or *evaluator* is provided the adapter operates in permissive
    mode — every action is allowed but a warning is emitted.

    Parameters
    ----------
    policy:
        Optional :class:`~agent_gov.policy.schema.PolicyConfig` to evaluate
        actions against.
    evaluator:
        Optional :class:`~agent_gov.policy.evaluator.PolicyEvaluator`.
        When *policy* is supplied and *evaluator* is omitted a default
        ``PolicyEvaluator()`` instance is created automatically.
    """

    def __init__(
        self,
        policy: Optional[PolicyConfig] = None,
        evaluator: Optional[PolicyEvaluator] = None,
    ) -> None:
        self._policy: Optional[PolicyConfig] = policy
        self._evaluator: Optional[PolicyEvaluator] = evaluator
        # Auto-create a default evaluator when a policy is provided.
        if self._policy is not None and self._evaluator is None:
            self._evaluator = PolicyEvaluator()
        self._audit_log: list[dict[str, object]] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record(
        self,
        event_type: str,
        result: dict[str, object],
        **context: object,
    ) -> None:
        """Append an entry to the audit log with a UTC timestamp."""
        entry: dict[str, object] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": event_type,
            "result": result,
            **context,
        }
        self._audit_log.append(entry)

    def _evaluate_action(
        self,
        action_type: str,
        action_context: dict[str, object],
    ) -> dict[str, object]:
        """Evaluate an action and record the decision to the audit log.

        When a *policy* and *evaluator* are configured the action is run
        through the evaluator and the result reflects the policy decision.
        When neither is configured the adapter falls back to permissive mode
        (allowed=True) and emits a ``WARNING`` log message.

        Parameters
        ----------
        action_type:
            Short label used as ``event_type`` in the audit log entry.
        action_context:
            Arbitrary dictionary describing the action to evaluate.

        Returns
        -------
        dict[str, object]
            Always contains at least ``"allowed"`` (bool) and ``"reason"``
            (str) keys.
        """
        if self._evaluator is not None and self._policy is not None:
            report = self._evaluator.evaluate(self._policy, action_context)
            if report.passed:
                result: dict[str, object] = {
                    "allowed": True,
                    "reason": f"Action passed policy {self._policy.name!r}.",
                }
            else:
                failed_messages = "; ".join(
                    v.message for v in report.failed_verdicts
                )
                result = {
                    "allowed": False,
                    "reason": (
                        f"Action blocked by policy {self._policy.name!r}: "
                        f"{failed_messages}"
                    ),
                    "violation_count": report.violation_count,
                    "highest_severity": report.highest_severity,
                }
        else:
            logger.warning(
                "GovernanceAdapter._evaluate_action called with no policy "
                "configured; running in permissive mode for action_type=%r.",
                action_type,
            )
            result = {
                "allowed": True,
                "reason": "No policy configured (permissive mode).",
            }

        self._record(action_type, result, **action_context)
        return result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def audit_log(self) -> list[dict[str, object]]:
        """Return a shallow copy of the audit log.

        Returns a copy so that callers cannot mutate the internal log.
        """
        return list(self._audit_log)

    def get_audit_log(self) -> list[dict[str, object]]:
        """Return the full audit log of governance decisions.

        Provided for backward compatibility with the original adapter API.
        Equivalent to the :attr:`audit_log` property.
        """
        return list(self._audit_log)

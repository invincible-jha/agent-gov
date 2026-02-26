"""Optional bridge to the agentcore-sdk event bus.

This module is guarded by a try/except ImportError so that agent-gov
remains installable without agentcore-sdk.  When agentcore-sdk is not
installed the :class:`AgentCoreBridge` is a no-op stub.

When agentcore-sdk IS installed, the bridge subscribes to agent action
events and evaluates them against the configured policy, logging each
result to the audit log.

Usage
-----
Install the optional dependency::

    pip install agent-gov[agentcore]

Then configure the bridge::

    from agent_gov.integration.agentcore_bridge import AgentCoreBridge
    from agent_gov.policy.loader import PolicyLoader
    from agent_gov.audit.logger import AuditLogger

    loader = PolicyLoader()
    policy = loader.load_file("policies/standard.yaml")
    audit_logger = AuditLogger("audit.jsonl")

    bridge = AgentCoreBridge(policy=policy, audit_logger=audit_logger)
    bridge.connect()
"""
from __future__ import annotations

import logging
from typing import Optional

from agent_gov.audit.logger import AuditLogger
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)

try:
    import agentcore  # type: ignore[import-not-found]

    _AGENTCORE_AVAILABLE = True
except ImportError:
    _AGENTCORE_AVAILABLE = False
    agentcore = None  # type: ignore[assignment]


class AgentCoreBridge:
    """Bridge between agentcore-sdk events and agent-gov policy evaluation.

    When agentcore-sdk is not installed, all methods are no-ops and
    :attr:`is_available` returns ``False``.

    Parameters
    ----------
    policy:
        The :class:`~agent_gov.policy.schema.PolicyConfig` to evaluate
        events against.
    audit_logger:
        Optional :class:`~agent_gov.audit.logger.AuditLogger` for
        persisting evaluation results.
    agent_id_field:
        Field name in event payloads used as the agent ID.  Defaults to
        ``"agent_id"``.
    """

    def __init__(
        self,
        policy: PolicyConfig,
        audit_logger: Optional[AuditLogger] = None,
        *,
        agent_id_field: str = "agent_id",
    ) -> None:
        self._policy = policy
        self._audit_logger = audit_logger
        self._agent_id_field = agent_id_field
        self._evaluator = PolicyEvaluator()
        self._connected = False

    @property
    def is_available(self) -> bool:
        """Return ``True`` when agentcore-sdk is installed."""
        return _AGENTCORE_AVAILABLE

    @property
    def is_connected(self) -> bool:
        """Return ``True`` when the bridge is actively subscribed."""
        return self._connected

    def connect(self) -> bool:
        """Subscribe to the agentcore event bus.

        Returns
        -------
        bool
            ``True`` when successfully connected, ``False`` when
            agentcore-sdk is not available.
        """
        if not _AGENTCORE_AVAILABLE:
            logger.warning(
                "agentcore-sdk is not installed. "
                "Install with: pip install agent-gov[agentcore]"
            )
            return False

        try:
            # Subscribe to agent action events via agentcore event bus.
            # The actual API depends on the agentcore-sdk version.
            event_bus = agentcore.get_event_bus()  # type: ignore[union-attr]
            event_bus.subscribe("agent.action", self._handle_event)
            self._connected = True
            logger.info(
                "AgentCoreBridge connected; evaluating against policy %r",
                self._policy.name,
            )
            return True
        except Exception:
            logger.exception("Failed to connect AgentCoreBridge to agentcore event bus.")
            return False

    def disconnect(self) -> None:
        """Unsubscribe from the agentcore event bus."""
        if not _AGENTCORE_AVAILABLE or not self._connected:
            return

        try:
            event_bus = agentcore.get_event_bus()  # type: ignore[union-attr]
            event_bus.unsubscribe("agent.action", self._handle_event)
            self._connected = False
            logger.info("AgentCoreBridge disconnected.")
        except Exception:
            logger.exception("Failed to disconnect AgentCoreBridge.")

    def _handle_event(self, event: dict[str, object]) -> None:
        """Handle an incoming agentcore event.

        Parameters
        ----------
        event:
            Raw event payload from the agentcore event bus.
        """
        try:
            report = self._evaluator.evaluate(self._policy, event)
            agent_id = str(event.get(self._agent_id_field, "unknown"))

            if self._audit_logger is not None:
                self._audit_logger.log_from_report(report, agent_id=agent_id)

            if not report.passed:
                logger.warning(
                    "Policy %r FAILED for agent %r: %d violation(s), highest severity=%s",
                    self._policy.name,
                    agent_id,
                    report.violation_count,
                    report.highest_severity,
                )
        except Exception:
            logger.exception(
                "AgentCoreBridge failed to evaluate event against policy %r.",
                self._policy.name,
            )

    def evaluate_event(
        self,
        event: dict[str, object],
        agent_id: str = "unknown",
    ) -> bool:
        """Manually evaluate a single event (without the event bus).

        Useful for testing the bridge configuration without a live
        agentcore connection.

        Parameters
        ----------
        event:
            Action payload to evaluate.
        agent_id:
            Agent identifier for audit logging.

        Returns
        -------
        bool
            ``True`` when the event passes the policy.
        """
        report = self._evaluator.evaluate(self._policy, event)
        if self._audit_logger is not None:
            self._audit_logger.log_from_report(report, agent_id=agent_id)
        return report.passed

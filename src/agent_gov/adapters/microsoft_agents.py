"""Microsoft Agents adapter for agent_gov."""
from __future__ import annotations

import logging
from typing import Optional

from agent_gov.adapters.action_mapper import map_microsoft_activity
from agent_gov.adapters.base import GovernanceAdapter
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class MicrosoftGovernance(GovernanceAdapter):
    """Governance and compliance adapter for Microsoft Agents.

    Evaluates Bot Framework activities, dialog steps, and conversation turns
    against a policy engine and maintains an immutable audit log.

    When *policy* and *evaluator* (or just *policy*) are supplied, each check
    is evaluated against the configured policy.  When neither is provided the
    adapter operates in permissive mode for backward compatibility.

    Parameters
    ----------
    policy_engine:
        Legacy parameter retained for backward compatibility.  Has no effect
        on policy evaluation; use *policy* and *evaluator* instead.
    policy:
        Optional :class:`~agent_gov.policy.schema.PolicyConfig` to enforce.
    evaluator:
        Optional :class:`~agent_gov.policy.evaluator.PolicyEvaluator`.
        A default instance is created automatically when *policy* is given.

    Usage::

        from agent_gov.adapters.microsoft_agents import MicrosoftGovernance
        adapter = MicrosoftGovernance()
    """

    def __init__(
        self,
        policy_engine: object = None,
        *,
        policy: Optional[PolicyConfig] = None,
        evaluator: Optional[PolicyEvaluator] = None,
    ) -> None:
        super().__init__(policy=policy, evaluator=evaluator)
        # Retained for backward compatibility; not used in evaluation.
        self.policy_engine = policy_engine
        logger.info("MicrosoftGovernance initialized.")

    def check_activity(
        self, activity_type: str, data: object
    ) -> dict[str, object]:
        """Evaluate a Bot Framework activity against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        text = str(data) if not isinstance(data, str) else data
        action_context = map_microsoft_activity(activity_type, text)
        return self._evaluate_action("check_activity", action_context)

    def check_dialog(self, dialog_id: str, step: str) -> dict[str, object]:
        """Evaluate a dialog waterfall step against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context: dict[str, object] = {
            "action_type": "microsoft_dialog",
            "dialog_id": dialog_id,
            "step": step,
        }
        return self._evaluate_action("check_dialog", action_context)

    def check_turn(self, turn_id: str, content: str) -> dict[str, object]:
        """Evaluate a conversation turn's content against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context: dict[str, object] = {
            "action_type": "microsoft_turn",
            "turn_id": turn_id,
            "content": content,
            "content_length": len(content),
        }
        return self._evaluate_action("check_turn", action_context)

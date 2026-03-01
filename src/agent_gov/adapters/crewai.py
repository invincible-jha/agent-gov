"""CrewAI adapter for agent_gov."""
from __future__ import annotations

import logging
from typing import Optional

from agent_gov.adapters.action_mapper import map_crewai_delegation, map_crewai_task
from agent_gov.adapters.base import GovernanceAdapter
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class CrewAIGovernance(GovernanceAdapter):
    """Governance and compliance adapter for CrewAI.

    Evaluates tasks, agent actions, and agent-to-agent delegations against a
    policy engine and records all decisions in an immutable audit log.

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

        from agent_gov.adapters.crewai import CrewAIGovernance
        adapter = CrewAIGovernance()
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
        logger.info("CrewAIGovernance initialized.")

    def check_task(
        self, task_name: str, task_input: object
    ) -> dict[str, object]:
        """Evaluate a CrewAI task against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context = map_crewai_task(
            task_description=str(task_name),
            agent_role=str(task_input) if not isinstance(task_input, dict) else "",
        )
        # Preserve the original task_name key for audit compatibility.
        action_context["task_name"] = task_name
        return self._evaluate_action("check_task", action_context)

    def check_agent_action(
        self, agent_name: str, action: str
    ) -> dict[str, object]:
        """Evaluate an agent action against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context: dict[str, object] = {
            "action_type": "crewai_agent_action",
            "agent_name": agent_name,
            "action": action,
        }
        return self._evaluate_action("check_agent_action", action_context)

    def check_delegation(
        self, from_agent: str, to_agent: str
    ) -> dict[str, object]:
        """Evaluate an agent-to-agent delegation against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context = map_crewai_delegation(from_agent, to_agent)
        return self._evaluate_action("check_delegation", action_context)

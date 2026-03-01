"""OpenAI Agents SDK adapter for agent_gov."""
from __future__ import annotations

import logging
from typing import Optional

from agent_gov.adapters.action_mapper import map_openai_message
from agent_gov.adapters.base import GovernanceAdapter
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class OpenAIGovernance(GovernanceAdapter):
    """Governance and compliance adapter for the OpenAI Agents SDK.

    Evaluates messages, tool uses, and agent handoffs against a policy engine
    and records all decisions in an immutable audit log.

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

        from agent_gov.adapters.openai_agents import OpenAIGovernance
        adapter = OpenAIGovernance()
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
        logger.info("OpenAIGovernance initialized.")

    def check_message(self, role: str, content: str) -> dict[str, object]:
        """Evaluate a message (by role) against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context = map_openai_message(role, content)
        return self._evaluate_action("check_message", action_context)

    def check_tool_use(
        self, tool_name: str, args: dict[str, object]
    ) -> dict[str, object]:
        """Evaluate a tool use request against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context: dict[str, object] = {
            "action_type": "openai_tool_use",
            "tool_name": tool_name,
            "args": args,
            "arg_count": len(args),
        }
        return self._evaluate_action("check_tool_use", action_context)

    def check_handoff(
        self, from_agent: str, to_agent: str
    ) -> dict[str, object]:
        """Evaluate an agent handoff against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context: dict[str, object] = {
            "action_type": "openai_handoff",
            "from_agent": from_agent,
            "to_agent": to_agent,
        }
        return self._evaluate_action("check_handoff", action_context)

"""Anthropic SDK adapter for agent_gov."""
from __future__ import annotations

import logging
from typing import Optional

from agent_gov.adapters.action_mapper import map_anthropic_message
from agent_gov.adapters.base import GovernanceAdapter
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class AnthropicGovernance(GovernanceAdapter):
    """Governance and compliance adapter for the Anthropic SDK.

    Evaluates messages, tool uses, and content blocks from Anthropic API
    interactions against a policy engine and maintains an immutable audit log.

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

        from agent_gov.adapters.anthropic_sdk import AnthropicGovernance
        adapter = AnthropicGovernance()
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
        logger.info("AnthropicGovernance initialized.")

    def check_message(self, role: str, content: str) -> dict[str, object]:
        """Evaluate an Anthropic message (by role) against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context = map_anthropic_message(role, content)
        return self._evaluate_action("check_message", action_context)

    def check_tool_use(
        self, tool_name: str, input: object  # noqa: A002
    ) -> dict[str, object]:
        """Evaluate an Anthropic tool_use content block against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        input_str = str(input) if input is not None else ""
        action_context: dict[str, object] = {
            "action_type": "anthropic_tool_use",
            "tool_name": tool_name,
            "input_preview": input_str[:200],
        }
        return self._evaluate_action("check_tool_use", action_context)

    def check_content(
        self, content_type: str, content: object
    ) -> dict[str, object]:
        """Evaluate a content block by type against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        content_str = str(content) if content is not None else ""
        action_context: dict[str, object] = {
            "action_type": "anthropic_content",
            "content_type": content_type,
            "content": content_str,
            "content_length": len(content_str),
        }
        return self._evaluate_action("check_content", action_context)

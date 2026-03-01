"""LangChain adapter for agent_gov."""
from __future__ import annotations

import logging
from typing import Optional

from agent_gov.adapters.action_mapper import map_langchain_prompt, map_langchain_tool_call
from agent_gov.adapters.base import GovernanceAdapter
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class LangChainGovernance(GovernanceAdapter):
    """Governance and compliance adapter for LangChain.

    Intercepts prompts, outputs, and tool calls to enforce policy rules and
    maintain an immutable audit log of all governance decisions.

    When *policy* and *evaluator* (or just *policy*) are supplied, each check
    is evaluated against the configured policy.  When neither is provided the
    adapter operates in permissive mode (all actions allowed) for backward
    compatibility.

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

        from agent_gov.adapters.langchain import LangChainGovernance
        adapter = LangChainGovernance()
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
        logger.info("LangChainGovernance initialized.")

    def check_prompt(self, prompt: str) -> dict[str, object]:
        """Evaluate a user or system prompt against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context = map_langchain_prompt(prompt)
        return self._evaluate_action("check_prompt", action_context)

    def check_output(self, output: str) -> dict[str, object]:
        """Evaluate an LLM output against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context: dict[str, object] = {
            "action_type": "langchain_output",
            "content": output,
            "content_length": len(output),
        }
        return self._evaluate_action("check_output", action_context)

    def check_tool_call(
        self, tool_name: str, args: dict[str, object]
    ) -> dict[str, object]:
        """Evaluate a tool call against the policy engine.

        Returns a governance decision with allowed status and reason.
        """
        action_context = map_langchain_tool_call(tool_name, args)
        return self._evaluate_action("check_tool_call", action_context)

"""Convenience API for agent-gov — 3-line quickstart.

Example
-------
::

    from agent_gov import GovernanceEngine
    engine = GovernanceEngine()
    result = engine.evaluate({"action": "file_read", "path": "/data.csv"})
    print(result.allowed)

"""
from __future__ import annotations

from typing import Any


class GovernanceEngine:
    """Zero-config governance engine for the 80% use case.

    Wraps PolicyEvaluator and PolicyConfig with sensible defaults.
    No policy file required — the default config applies keyword
    blocking and basic cost limits out of the box.

    Parameters
    ----------
    policy_path:
        Optional path to a YAML policy file. If None, a permissive
        default policy is used (no rules, all actions allowed).

    Example
    -------
    ::

        from agent_gov import GovernanceEngine
        engine = GovernanceEngine()
        result = engine.evaluate({"action": "search", "query": "Python"})
        print(result.allowed)  # True
    """

    def __init__(self, policy_path: str | None = None) -> None:
        from agent_gov.policy.evaluator import PolicyEvaluator
        from agent_gov.policy.schema import PolicyConfig, RuleConfig

        self._evaluator = PolicyEvaluator()

        if policy_path is not None:
            from agent_gov.policy.loader import PolicyLoader
            loader = PolicyLoader()
            self._policy = loader.load_file(policy_path)
        else:
            self._policy = PolicyConfig(
                name="quickstart-default",
                version="1.0",
                rules=[],
            )

    def evaluate(self, action: dict[str, Any]) -> Any:
        """Evaluate an agent action against the active policy.

        Parameters
        ----------
        action:
            Dict describing the agent action. Common keys include
            ``action`` (action type), ``agent_id``, and action-specific
            fields like ``query`` or ``path``.

        Returns
        -------
        EvaluationReport
            Report with ``.passed`` bool and per-rule verdicts.

        Example
        -------
        ::

            engine = GovernanceEngine()
            report = engine.evaluate({"action": "search", "query": "test"})
            assert report.passed
        """
        return self._evaluator.evaluate(self._policy, action)

    @property
    def policy(self) -> Any:
        """The active PolicyConfig."""
        return self._policy

    def __repr__(self) -> str:
        return f"GovernanceEngine(policy={self._policy.name!r})"

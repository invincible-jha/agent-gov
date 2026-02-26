"""PolicyEvaluator — orchestrates rule evaluation against a policy.

The evaluator resolves rule names to registered
:class:`~agent_gov.policy.rule.PolicyRule` instances and runs each enabled
rule in declaration order.

Example
-------
::

    from agent_gov.policy.evaluator import PolicyEvaluator
    from agent_gov.policy.loader import PolicyLoader

    loader = PolicyLoader()
    policy = loader.load_file("policies/standard.yaml")

    evaluator = PolicyEvaluator()
    report = evaluator.evaluate(policy, {"type": "search", "query": "test"})

    if not report.passed:
        for verdict in report.failed_verdicts:
            print(verdict.message)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from agent_gov.policy.result import EvaluationReport
from agent_gov.policy.rule import PolicyRule, RuleVerdict
from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)


class RuleResolutionError(Exception):
    """Raised when a rule type cannot be resolved to a registered class."""

    def __init__(self, rule_type: str) -> None:
        self.rule_type = rule_type
        super().__init__(
            f"No rule implementation registered for type {rule_type!r}. "
            "Register the rule with the rule registry before evaluating."
        )


class PolicyEvaluator:
    """Runs all enabled rules in a policy against an agent action.

    The evaluator maintains an internal rule registry mapping rule type
    strings to :class:`~agent_gov.policy.rule.PolicyRule` instances.
    Built-in rules are registered automatically; additional rules can be
    injected via :meth:`register_rule`.

    Parameters
    ----------
    strict:
        When ``True``, an unresolvable rule type raises
        :exc:`RuleResolutionError`.  When ``False``, unresolvable rules are
        logged as warnings and skipped.
    """

    def __init__(self, *, strict: bool = True) -> None:
        self._strict = strict
        self._rules: dict[str, PolicyRule] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register the four built-in rule implementations."""
        from agent_gov.rules.cost_limit import CostLimitRule
        from agent_gov.rules.keyword_block import KeywordBlockRule
        from agent_gov.rules.pii_check import PiiCheckRule
        from agent_gov.rules.role_check import RoleCheckRule

        for rule_cls in (PiiCheckRule, RoleCheckRule, CostLimitRule, KeywordBlockRule):
            instance = rule_cls()
            self._rules[instance.name] = instance

    def register_rule(self, rule: PolicyRule) -> None:
        """Register a custom rule implementation.

        Parameters
        ----------
        rule:
            An instantiated :class:`~agent_gov.policy.rule.PolicyRule`.
            If a rule with the same name is already registered it is replaced.
        """
        logger.debug("Registering rule %r", rule.name)
        self._rules[rule.name] = rule

    def list_rule_types(self) -> list[str]:
        """Return sorted list of all registered rule type names."""
        return sorted(self._rules)

    def evaluate(
        self,
        policy: PolicyConfig,
        action: dict[str, object],
    ) -> EvaluationReport:
        """Evaluate an agent action against all enabled rules in a policy.

        Parameters
        ----------
        policy:
            Validated :class:`~agent_gov.policy.schema.PolicyConfig` to
            evaluate the action against.
        action:
            Arbitrary dictionary describing the agent action.

        Returns
        -------
        EvaluationReport
            Aggregated result; ``report.passed`` is ``True`` only when every
            enabled rule passes.

        Raises
        ------
        RuleResolutionError
            If :attr:`strict` is ``True`` and a rule type cannot be resolved.
        """
        verdicts: list[RuleVerdict] = []
        overall_passed = True
        timestamp = datetime.now(timezone.utc)

        for rule_config in policy.enabled_rules:
            rule = self._rules.get(rule_config.type)
            if rule is None:
                if self._strict:
                    raise RuleResolutionError(rule_config.type)
                logger.warning(
                    "Rule type %r not found; skipping rule %r in policy %r",
                    rule_config.type,
                    rule_config.name,
                    policy.name,
                )
                continue

            try:
                verdict = rule.evaluate(action, dict(rule_config.params))
            except Exception:
                logger.exception(
                    "Rule %r raised an unexpected exception evaluating action; "
                    "marking as failed.",
                    rule_config.name,
                )
                verdict = RuleVerdict(
                    rule_name=rule_config.name,
                    passed=False,
                    severity=rule_config.severity.value,
                    message=f"Rule {rule_config.name!r} raised an unexpected exception.",
                )

            # Apply the config-level severity override (config wins over rule default).
            verdict.rule_name = rule_config.name
            verdict.severity = rule_config.severity.value

            verdicts.append(verdict)
            if not verdict.passed:
                overall_passed = False
                logger.info(
                    "Policy %r rule %r FAILED: %s",
                    policy.name,
                    rule_config.name,
                    verdict.message,
                )

        report = EvaluationReport(
            policy_name=policy.name,
            action=action,
            verdicts=verdicts,
            passed=overall_passed,
            timestamp=timestamp,
        )
        logger.debug("Evaluation complete: %s", report.summary())
        return report

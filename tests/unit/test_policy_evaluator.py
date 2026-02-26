"""Unit tests for agent_gov.policy.evaluator.PolicyEvaluator.

Covers rule registration, evaluation with built-in rules, strict vs. lenient
mode, exception handling inside rules, and severity override from config.
"""
from __future__ import annotations

import pytest

from agent_gov.policy.evaluator import PolicyEvaluator, RuleResolutionError
from agent_gov.policy.result import EvaluationReport
from agent_gov.policy.rule import PolicyRule, RuleVerdict
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity


def _make_policy(rules: list[RuleConfig], name: str = "test-policy") -> PolicyConfig:
    return PolicyConfig(name=name, rules=rules)


class _AlwaysPassRule(PolicyRule):
    name = "always_pass"

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        return RuleVerdict(rule_name=self.name, passed=True, severity="low")


class _AlwaysFailRule(PolicyRule):
    name = "always_fail"

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        return RuleVerdict(rule_name=self.name, passed=False, severity="high", message="Always fails.")


class _ExplodingRule(PolicyRule):
    name = "exploding"

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        raise RuntimeError("Boom!")


class TestPolicyEvaluatorBuiltins:
    def test_builtin_rules_are_registered(self) -> None:
        evaluator = PolicyEvaluator()
        rule_types = evaluator.list_rule_types()
        assert "pii_check" in rule_types
        assert "role_check" in rule_types
        assert "cost_limit" in rule_types
        assert "keyword_block" in rule_types

    def test_list_rule_types_is_sorted(self) -> None:
        evaluator = PolicyEvaluator()
        types = evaluator.list_rule_types()
        assert types == sorted(types)


class TestPolicyEvaluatorRegistration:
    def test_register_custom_rule(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysPassRule())
        assert "always_pass" in evaluator.list_rule_types()

    def test_register_custom_rule_replaces_existing(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysPassRule())
        evaluator.register_rule(_AlwaysPassRule())  # Should not raise
        assert evaluator.list_rule_types().count("always_pass") == 1


class TestPolicyEvaluatorEvaluate:
    def test_empty_policy_passes(self) -> None:
        evaluator = PolicyEvaluator()
        policy = _make_policy([])
        report = evaluator.evaluate(policy, {"type": "search"})
        assert report.passed is True
        assert report.verdicts == []

    def test_single_passing_rule(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysPassRule())
        policy = _make_policy([
            RuleConfig(name="pass-rule", type="always_pass", severity=Severity.LOW)
        ])
        report = evaluator.evaluate(policy, {})
        assert report.passed is True
        assert len(report.verdicts) == 1

    def test_single_failing_rule(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysFailRule())
        policy = _make_policy([
            RuleConfig(name="fail-rule", type="always_fail")
        ])
        report = evaluator.evaluate(policy, {})
        assert report.passed is False
        assert report.violation_count == 1

    def test_mixed_rules_fails_when_any_fails(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysPassRule())
        evaluator.register_rule(_AlwaysFailRule())
        policy = _make_policy([
            RuleConfig(name="pass", type="always_pass"),
            RuleConfig(name="fail", type="always_fail"),
        ])
        report = evaluator.evaluate(policy, {})
        assert report.passed is False
        assert report.violation_count == 1

    def test_disabled_rule_is_skipped(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysFailRule())
        policy = _make_policy([
            RuleConfig(name="fail-rule", type="always_fail", enabled=False)
        ])
        report = evaluator.evaluate(policy, {})
        assert report.passed is True
        assert report.verdicts == []

    def test_returns_evaluation_report_instance(self) -> None:
        evaluator = PolicyEvaluator()
        policy = _make_policy([])
        report = evaluator.evaluate(policy, {})
        assert isinstance(report, EvaluationReport)

    def test_report_policy_name_matches(self) -> None:
        evaluator = PolicyEvaluator()
        policy = _make_policy([], name="named-policy")
        report = evaluator.evaluate(policy, {})
        assert report.policy_name == "named-policy"

    def test_report_action_matches(self) -> None:
        evaluator = PolicyEvaluator()
        policy = _make_policy([])
        action = {"type": "write", "content": "hello"}
        report = evaluator.evaluate(policy, action)
        assert report.action == action

    def test_severity_override_from_rule_config(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysFailRule())
        policy = _make_policy([
            RuleConfig(name="fail-rule", type="always_fail", severity=Severity.CRITICAL)
        ])
        report = evaluator.evaluate(policy, {})
        assert report.verdicts[0].severity == "critical"

    def test_rule_name_set_from_config(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_AlwaysPassRule())
        policy = _make_policy([
            RuleConfig(name="my-custom-name", type="always_pass")
        ])
        report = evaluator.evaluate(policy, {})
        assert report.verdicts[0].rule_name == "my-custom-name"


class TestPolicyEvaluatorStrictMode:
    def test_strict_mode_raises_on_unknown_rule(self) -> None:
        evaluator = PolicyEvaluator(strict=True)
        policy = _make_policy([
            RuleConfig(name="ghost", type="nonexistent_rule")
        ])
        with pytest.raises(RuleResolutionError) as exc_info:
            evaluator.evaluate(policy, {})
        assert exc_info.value.rule_type == "nonexistent_rule"

    def test_lenient_mode_skips_unknown_rule(self) -> None:
        evaluator = PolicyEvaluator(strict=False)
        policy = _make_policy([
            RuleConfig(name="ghost", type="nonexistent_rule")
        ])
        report = evaluator.evaluate(policy, {})
        # Lenient mode: unknown rule is skipped, so no verdicts
        assert report.passed is True
        assert report.verdicts == []

    def test_rule_resolution_error_contains_type(self) -> None:
        error = RuleResolutionError("bad_type")
        assert "bad_type" in str(error)
        assert error.rule_type == "bad_type"


class TestPolicyEvaluatorExceptionHandling:
    def test_rule_exception_marks_verdict_as_failed(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_ExplodingRule())
        policy = _make_policy([
            RuleConfig(name="explodes", type="exploding")
        ])
        report = evaluator.evaluate(policy, {})
        assert report.passed is False
        assert report.violation_count == 1

    def test_rule_exception_verdict_message_mentions_rule_name(self) -> None:
        evaluator = PolicyEvaluator()
        evaluator.register_rule(_ExplodingRule())
        policy = _make_policy([
            RuleConfig(name="boom-rule", type="exploding")
        ])
        report = evaluator.evaluate(policy, {})
        assert "boom-rule" in report.verdicts[0].message

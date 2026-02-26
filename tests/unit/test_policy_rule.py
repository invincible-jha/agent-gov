"""Unit tests for agent_gov.policy.rule.

Covers RuleVerdict dataclass serialisation and the PolicyRule abstract base
class contract, including validate_config default behaviour.
"""
from __future__ import annotations

import pytest

from agent_gov.policy.rule import PolicyRule, RuleVerdict


class TestRuleVerdict:
    def test_default_construction(self) -> None:
        verdict = RuleVerdict()
        assert verdict.rule_name == ""
        assert verdict.passed is True
        assert verdict.severity == "medium"
        assert verdict.message == ""
        assert verdict.details == {}

    def test_explicit_construction(self) -> None:
        verdict = RuleVerdict(
            rule_name="pii_check",
            passed=False,
            severity="high",
            message="PII found",
            details={"count": 3},
        )
        assert verdict.rule_name == "pii_check"
        assert verdict.passed is False
        assert verdict.severity == "high"
        assert verdict.message == "PII found"
        assert verdict.details["count"] == 3

    def test_to_dict_keys(self) -> None:
        verdict = RuleVerdict(rule_name="r", passed=True, severity="low")
        result = verdict.to_dict()
        assert set(result.keys()) == {"rule_name", "passed", "severity", "message", "details"}

    def test_to_dict_values(self) -> None:
        verdict = RuleVerdict(
            rule_name="test",
            passed=False,
            severity="critical",
            message="bad",
            details={"x": 1},
        )
        result = verdict.to_dict()
        assert result["rule_name"] == "test"
        assert result["passed"] is False
        assert result["severity"] == "critical"
        assert result["message"] == "bad"
        assert result["details"] == {"x": 1}

    def test_details_default_is_independent_per_instance(self) -> None:
        v1 = RuleVerdict()
        v2 = RuleVerdict()
        v1.details["key"] = "value"
        assert "key" not in v2.details


class TestPolicyRuleAbstract:
    def test_cannot_instantiate_abstract_class(self) -> None:
        with pytest.raises(TypeError):
            PolicyRule()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_evaluate(self) -> None:
        class IncompleteRule(PolicyRule):
            name = "incomplete"
            # Missing evaluate implementation

        with pytest.raises(TypeError):
            IncompleteRule()  # type: ignore[abstract]

    def test_concrete_subclass_is_instantiable(self) -> None:
        class AlwaysPassRule(PolicyRule):
            name = "always_pass"

            def evaluate(
                self,
                action: dict[str, object],
                config: dict[str, object],
            ) -> RuleVerdict:
                return RuleVerdict(rule_name=self.name, passed=True)

        rule = AlwaysPassRule()
        assert rule.name == "always_pass"

    def test_evaluate_returns_rule_verdict(self) -> None:
        class SimpleRule(PolicyRule):
            name = "simple"

            def evaluate(
                self,
                action: dict[str, object],
                config: dict[str, object],
            ) -> RuleVerdict:
                return RuleVerdict(rule_name=self.name, passed=True)

        rule = SimpleRule()
        verdict = rule.evaluate({}, {})
        assert isinstance(verdict, RuleVerdict)

    def test_validate_config_default_returns_empty_list(self) -> None:
        class ConcreteRule(PolicyRule):
            name = "concrete"

            def evaluate(
                self,
                action: dict[str, object],
                config: dict[str, object],
            ) -> RuleVerdict:
                return RuleVerdict()

        rule = ConcreteRule()
        errors = rule.validate_config({"any_key": "any_value"})
        assert errors == []

    def test_repr_contains_class_name_and_rule_name(self) -> None:
        class MyRule(PolicyRule):
            name = "my_rule"

            def evaluate(
                self,
                action: dict[str, object],
                config: dict[str, object],
            ) -> RuleVerdict:
                return RuleVerdict()

        rule = MyRule()
        representation = repr(rule)
        assert "MyRule" in representation
        assert "my_rule" in representation

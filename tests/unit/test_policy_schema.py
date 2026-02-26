"""Unit tests for agent_gov.policy.schema.

Covers Severity enum, RuleConfig, and PolicyConfig Pydantic models including
validation, defaults, extra-field rejection, and the enabled_rules property.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity


class TestSeverityEnum:
    def test_all_values_are_strings(self) -> None:
        for member in Severity:
            assert isinstance(member.value, str)

    def test_low_value(self) -> None:
        assert Severity.LOW.value == "low"

    def test_medium_value(self) -> None:
        assert Severity.MEDIUM.value == "medium"

    def test_high_value(self) -> None:
        assert Severity.HIGH.value == "high"

    def test_critical_value(self) -> None:
        assert Severity.CRITICAL.value == "critical"

    def test_four_members(self) -> None:
        assert len(Severity) == 4


class TestRuleConfig:
    def test_minimal_valid_construction(self) -> None:
        rule = RuleConfig(name="my-rule", type="pii_check")
        assert rule.name == "my-rule"
        assert rule.type == "pii_check"

    def test_default_enabled_is_true(self) -> None:
        rule = RuleConfig(name="r", type="role_check")
        assert rule.enabled is True

    def test_default_severity_is_medium(self) -> None:
        rule = RuleConfig(name="r", type="role_check")
        assert rule.severity == Severity.MEDIUM

    def test_default_params_is_empty_dict(self) -> None:
        rule = RuleConfig(name="r", type="pii_check")
        assert rule.params == {}

    def test_custom_severity(self) -> None:
        rule = RuleConfig(name="r", type="pii_check", severity=Severity.HIGH)
        assert rule.severity == Severity.HIGH

    def test_severity_from_string(self) -> None:
        rule = RuleConfig(name="r", type="pii_check", severity="critical")  # type: ignore[arg-type]
        assert rule.severity == Severity.CRITICAL

    def test_params_populated(self) -> None:
        rule = RuleConfig(name="r", type="pii_check", params={"check_ssn": True})
        assert rule.params["check_ssn"] is True

    def test_disabled_rule(self) -> None:
        rule = RuleConfig(name="r", type="pii_check", enabled=False)
        assert rule.enabled is False

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RuleConfig(name="r", type="pii_check", unknown_field="bad")  # type: ignore[call-arg]

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            RuleConfig(type="pii_check")  # type: ignore[call-arg]

    def test_missing_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            RuleConfig(name="r")  # type: ignore[call-arg]


class TestPolicyConfig:
    def test_minimal_valid_construction(self) -> None:
        policy = PolicyConfig(name="my-policy")
        assert policy.name == "my-policy"

    def test_default_version(self) -> None:
        policy = PolicyConfig(name="p")
        assert policy.version == "1.0"

    def test_default_description_is_empty(self) -> None:
        policy = PolicyConfig(name="p")
        assert policy.description == ""

    def test_default_rules_is_empty_list(self) -> None:
        policy = PolicyConfig(name="p")
        assert policy.rules == []

    def test_default_metadata_is_empty_dict(self) -> None:
        policy = PolicyConfig(name="p")
        assert policy.metadata == {}

    def test_custom_version(self) -> None:
        policy = PolicyConfig(name="p", version="2.3")
        assert policy.version == "2.3"

    def test_rules_populated(self) -> None:
        rule = RuleConfig(name="r", type="pii_check")
        policy = PolicyConfig(name="p", rules=[rule])
        assert len(policy.rules) == 1
        assert policy.rules[0].name == "r"

    def test_metadata_populated(self) -> None:
        policy = PolicyConfig(name="p", metadata={"author": "alice"})
        assert policy.metadata["author"] == "alice"

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PolicyConfig(name="p", alien_field=True)  # type: ignore[call-arg]

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            PolicyConfig()  # type: ignore[call-arg]

    def test_enabled_rules_excludes_disabled(self) -> None:
        enabled_rule = RuleConfig(name="enabled", type="pii_check", enabled=True)
        disabled_rule = RuleConfig(name="disabled", type="role_check", enabled=False)
        policy = PolicyConfig(name="p", rules=[enabled_rule, disabled_rule])
        assert len(policy.enabled_rules) == 1
        assert policy.enabled_rules[0].name == "enabled"

    def test_enabled_rules_all_enabled(self) -> None:
        rules = [
            RuleConfig(name="r1", type="pii_check"),
            RuleConfig(name="r2", type="role_check"),
        ]
        policy = PolicyConfig(name="p", rules=rules)
        assert len(policy.enabled_rules) == 2

    def test_enabled_rules_all_disabled_returns_empty(self) -> None:
        rules = [
            RuleConfig(name="r1", type="pii_check", enabled=False),
            RuleConfig(name="r2", type="role_check", enabled=False),
        ]
        policy = PolicyConfig(name="p", rules=rules)
        assert policy.enabled_rules == []

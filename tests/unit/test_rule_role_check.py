"""Unit tests for agent_gov.rules.role_check.RoleCheckRule.

Tests allowed/denied roles, wildcard pattern matching, missing role field,
single string roles, list roles, and config validation.
"""
from __future__ import annotations

import pytest

from agent_gov.rules.role_check import RoleCheckRule
from agent_gov.policy.rule import RuleVerdict


@pytest.fixture()
def role_rule() -> RoleCheckRule:
    return RoleCheckRule()


class TestRoleCheckRuleName:
    def test_rule_name(self, role_rule: RoleCheckRule) -> None:
        assert role_rule.name == "role_check"


class TestRoleCheckAllowedRoles:
    def test_exact_match_passes(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "admin"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert verdict.passed is True

    def test_exact_match_in_list_passes(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "operator"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin", "operator"]})
        assert verdict.passed is True

    def test_non_matching_role_fails(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "viewer"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert verdict.passed is False

    def test_agent_with_list_of_roles_one_matches(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": ["viewer", "admin"]}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert verdict.passed is True

    def test_agent_with_list_of_roles_none_match_fails(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": ["viewer", "guest"]}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin", "operator"]})
        assert verdict.passed is False


class TestRoleCheckWildcardPatterns:
    def test_wildcard_prefix_matches(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "ops:deploy"}
        verdict = role_rule.evaluate(action, {"required_roles": ["ops:*"]})
        assert verdict.passed is True

    def test_wildcard_matches_any(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "anything"}
        verdict = role_rule.evaluate(action, {"required_roles": ["*"]})
        assert verdict.passed is True

    def test_wildcard_no_match(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "viewer"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin:*"]})
        assert verdict.passed is False

    def test_exact_and_wildcard_combined(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "ops:read"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin", "ops:*"]})
        assert verdict.passed is True


class TestRoleCheckMissingField:
    def test_missing_role_field_fails(self, role_rule: RoleCheckRule) -> None:
        action = {"type": "search"}  # No role field
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert verdict.passed is False

    def test_missing_role_field_message_mentions_field(self, role_rule: RoleCheckRule) -> None:
        action = {}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert "agent_role" in verdict.message

    def test_custom_role_field_used(self, role_rule: RoleCheckRule) -> None:
        action = {"user_role": "admin"}
        verdict = role_rule.evaluate(action, {
            "required_roles": ["admin"],
            "agent_role_field": "user_role",
        })
        assert verdict.passed is True

    def test_custom_role_field_missing_fails(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "admin"}
        verdict = role_rule.evaluate(action, {
            "required_roles": ["admin"],
            "agent_role_field": "user_role",
        })
        assert verdict.passed is False


class TestRoleCheckEmptyRequiredRoles:
    def test_no_required_roles_passes_by_default(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "viewer"}
        verdict = role_rule.evaluate(action, {"required_roles": []})
        assert verdict.passed is True

    def test_missing_required_roles_key_passes(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "viewer"}
        verdict = role_rule.evaluate(action, {})
        assert verdict.passed is True


class TestRoleCheckVerdictDetails:
    def test_passing_verdict_details_has_agent_roles(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "admin"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert "agent_roles" in verdict.details

    def test_failing_verdict_details_has_required_roles(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "guest"}
        verdict = role_rule.evaluate(action, {"required_roles": ["admin"]})
        assert "required_roles" in verdict.details

    def test_passing_verdict_details_has_matched_pattern(self, role_rule: RoleCheckRule) -> None:
        action = {"agent_role": "ops:deploy"}
        verdict = role_rule.evaluate(action, {"required_roles": ["ops:*"]})
        assert verdict.details.get("matched_pattern") == "ops:*"


class TestRoleCheckValidateConfig:
    def test_valid_config_returns_no_errors(self, role_rule: RoleCheckRule) -> None:
        errors = role_rule.validate_config({"required_roles": ["admin"]})
        assert errors == []

    def test_missing_required_roles_returns_error(self, role_rule: RoleCheckRule) -> None:
        errors = role_rule.validate_config({})
        assert len(errors) >= 1
        assert any("required_roles" in e for e in errors)

    def test_empty_required_roles_list_returns_error(self, role_rule: RoleCheckRule) -> None:
        errors = role_rule.validate_config({"required_roles": []})
        assert len(errors) >= 1

    def test_non_list_required_roles_returns_error(self, role_rule: RoleCheckRule) -> None:
        errors = role_rule.validate_config({"required_roles": "admin"})
        assert len(errors) >= 1

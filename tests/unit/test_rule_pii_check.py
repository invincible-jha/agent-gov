"""Unit tests for agent_gov.rules.pii_check.PiiCheckRule.

Each PII pattern type is tested with known triggering and non-triggering
inputs, including nested dict and list scanning, selective config flags,
and config validation.
"""
from __future__ import annotations

import pytest

from agent_gov.rules.pii_check import PiiCheckRule
from agent_gov.policy.rule import RuleVerdict


@pytest.fixture()
def pii_rule() -> PiiCheckRule:
    return PiiCheckRule()


class TestPiiCheckRuleName:
    def test_rule_name(self, pii_rule: PiiCheckRule) -> None:
        assert pii_rule.name == "pii_check"


class TestEmailDetection:
    def test_detects_simple_email(self, pii_rule: PiiCheckRule) -> None:
        action = {"message": "Contact user@example.com for details."}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert verdict.passed is False
        assert "email" in verdict.details.get("detected_types", [])

    def test_detects_email_with_subdomain(self, pii_rule: PiiCheckRule) -> None:
        action = {"body": "Reach alice.jones+tag@mail.corp.org now."}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert verdict.passed is False

    def test_no_email_in_clean_text(self, pii_rule: PiiCheckRule) -> None:
        action = {"message": "No email address here."}
        verdict = pii_rule.evaluate(action, {"check_email": True, "check_ssn": False,
                                             "check_phone": False, "check_credit_card": False})
        assert verdict.passed is True

    def test_email_check_disabled(self, pii_rule: PiiCheckRule) -> None:
        action = {"message": "Contact user@example.com"}
        verdict = pii_rule.evaluate(action, {"check_email": False, "check_ssn": False,
                                             "check_phone": False, "check_credit_card": False})
        assert verdict.passed is True


class TestSsnDetection:
    def test_detects_ssn_with_dashes(self, pii_rule: PiiCheckRule) -> None:
        action = {"field": "SSN is 123-45-6789"}
        verdict = pii_rule.evaluate(action, {"check_ssn": True, "check_email": False,
                                             "check_phone": False, "check_credit_card": False})
        assert verdict.passed is False
        assert "ssn" in verdict.details.get("detected_types", [])

    def test_detects_ssn_with_spaces(self, pii_rule: PiiCheckRule) -> None:
        action = {"field": "My SSN 234 56 7890"}
        verdict = pii_rule.evaluate(action, {"check_ssn": True, "check_email": False,
                                             "check_phone": False, "check_credit_card": False})
        assert verdict.passed is False

    def test_no_ssn_in_clean_text(self, pii_rule: PiiCheckRule) -> None:
        action = {"field": "Reference number 999-99-9999 is invalid by rule"}
        # SSN regex excludes 9xx numbers
        verdict = pii_rule.evaluate(action, {"check_ssn": True, "check_email": False,
                                             "check_phone": False, "check_credit_card": False})
        # 999-99-9999 starts with 9, should be excluded by the regex
        assert verdict.passed is True

    def test_ssn_check_disabled(self, pii_rule: PiiCheckRule) -> None:
        action = {"field": "SSN is 123-45-6789"}
        verdict = pii_rule.evaluate(action, {"check_ssn": False, "check_email": False,
                                             "check_phone": False, "check_credit_card": False})
        assert verdict.passed is True


class TestPhoneDetection:
    def test_detects_us_phone_with_dashes(self, pii_rule: PiiCheckRule) -> None:
        action = {"contact": "Call 555-867-5309 now."}
        verdict = pii_rule.evaluate(action, {"check_phone": True, "check_email": False,
                                             "check_ssn": False, "check_credit_card": False})
        assert verdict.passed is False
        assert "phone" in verdict.details.get("detected_types", [])

    def test_detects_us_phone_with_parens(self, pii_rule: PiiCheckRule) -> None:
        action = {"contact": "Office: (800) 123-4567"}
        verdict = pii_rule.evaluate(action, {"check_phone": True, "check_email": False,
                                             "check_ssn": False, "check_credit_card": False})
        assert verdict.passed is False

    def test_detects_phone_with_country_code(self, pii_rule: PiiCheckRule) -> None:
        action = {"contact": "Mobile: +1 212 555 1234"}
        verdict = pii_rule.evaluate(action, {"check_phone": True, "check_email": False,
                                             "check_ssn": False, "check_credit_card": False})
        assert verdict.passed is False

    def test_phone_check_disabled(self, pii_rule: PiiCheckRule) -> None:
        action = {"contact": "Call 555-867-5309"}
        verdict = pii_rule.evaluate(action, {"check_phone": False, "check_email": False,
                                             "check_ssn": False, "check_credit_card": False})
        assert verdict.passed is True


class TestCreditCardDetection:
    def test_detects_16_digit_credit_card(self, pii_rule: PiiCheckRule) -> None:
        action = {"payment": "Card: 4111111111111111"}
        verdict = pii_rule.evaluate(action, {"check_credit_card": True, "check_email": False,
                                             "check_ssn": False, "check_phone": False})
        assert verdict.passed is False
        assert "credit_card" in verdict.details.get("detected_types", [])

    def test_detects_card_with_dashes(self, pii_rule: PiiCheckRule) -> None:
        action = {"payment": "Card: 4111-1111-1111-1111"}
        verdict = pii_rule.evaluate(action, {"check_credit_card": True, "check_email": False,
                                             "check_ssn": False, "check_phone": False})
        assert verdict.passed is False

    def test_credit_card_check_disabled(self, pii_rule: PiiCheckRule) -> None:
        action = {"payment": "4111111111111111"}
        verdict = pii_rule.evaluate(action, {"check_credit_card": False, "check_email": False,
                                             "check_ssn": False, "check_phone": False})
        assert verdict.passed is True


class TestPiiCheckNestedScanning:
    def test_scans_nested_dict_values(self, pii_rule: PiiCheckRule) -> None:
        action = {"user": {"email": "alice@example.com"}}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert verdict.passed is False

    def test_scans_list_string_values(self, pii_rule: PiiCheckRule) -> None:
        action = {"contacts": ["alice@example.com", "bob@example.com"]}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert verdict.passed is False
        assert verdict.details.get("match_count", 0) >= 2

    def test_scans_list_of_dicts(self, pii_rule: PiiCheckRule) -> None:
        action = {"records": [{"email": "user@domain.io"}]}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert verdict.passed is False

    def test_clean_action_passes(self, pii_rule: PiiCheckRule) -> None:
        action = {"query": "What is the weather in London?", "type": "search"}
        verdict = pii_rule.evaluate(action, {})
        assert verdict.passed is True

    def test_no_patterns_enabled_passes(self, pii_rule: PiiCheckRule) -> None:
        action = {"message": "user@example.com 123-45-6789 4111111111111111"}
        verdict = pii_rule.evaluate(action, {
            "check_email": False, "check_ssn": False,
            "check_phone": False, "check_credit_card": False
        })
        assert verdict.passed is True


class TestPiiCheckVerdictDetails:
    def test_failed_verdict_has_detected_types(self, pii_rule: PiiCheckRule) -> None:
        action = {"body": "Contact user@example.com"}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert "detected_types" in verdict.details

    def test_failed_verdict_has_match_count(self, pii_rule: PiiCheckRule) -> None:
        action = {"body": "Contact user@example.com"}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert verdict.details["match_count"] >= 1

    def test_failed_verdict_has_fields(self, pii_rule: PiiCheckRule) -> None:
        action = {"body": "Contact user@example.com"}
        verdict = pii_rule.evaluate(action, {"check_email": True})
        assert "fields" in verdict.details

    def test_passing_verdict_message(self, pii_rule: PiiCheckRule) -> None:
        action = {"query": "safe query"}
        verdict = pii_rule.evaluate(action, {
            "check_email": False, "check_ssn": False,
            "check_phone": False, "check_credit_card": False
        })
        assert "No PII detected" in verdict.message


class TestPiiCheckValidateConfig:
    def test_valid_config_returns_no_errors(self, pii_rule: PiiCheckRule) -> None:
        errors = pii_rule.validate_config({"check_email": True, "check_ssn": False})
        assert errors == []

    def test_unknown_key_returns_error(self, pii_rule: PiiCheckRule) -> None:
        errors = pii_rule.validate_config({"unknown_param": True})
        assert len(errors) == 1
        assert "unknown_param" in errors[0]

    def test_empty_config_returns_no_errors(self, pii_rule: PiiCheckRule) -> None:
        errors = pii_rule.validate_config({})
        assert errors == []

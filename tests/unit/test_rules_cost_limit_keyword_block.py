"""Tests for agent_gov.rules.cost_limit and agent_gov.rules.keyword_block."""
from __future__ import annotations

import pytest

from agent_gov.rules.cost_limit import CostLimitRule
from agent_gov.rules.keyword_block import (
    KeywordBlockRule,
    _extract_strings,
    _extract_strings_from_list,
    _matches,
)


# ---------------------------------------------------------------------------
# CostLimitRule
# ---------------------------------------------------------------------------


class TestCostLimitRule:
    def test_passes_when_no_limits_configured(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({"cost": 999.0}, {})
        assert verdict.passed

    def test_passes_within_per_action_limit(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({"cost": 0.05}, {"max_cost_per_action": 0.10})
        assert verdict.passed

    def test_fails_exceeding_per_action_limit(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({"cost": 0.50}, {"max_cost_per_action": 0.10})
        assert not verdict.passed
        assert "per-action limit" in verdict.message

    def test_fails_on_negative_cost(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({"cost": -1.0}, {"max_cost_per_action": 10.0})
        assert not verdict.passed
        assert "negative" in verdict.message

    def test_fails_on_non_numeric_cost(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({"cost": "expensive"}, {})
        assert not verdict.passed
        assert "non-numeric" in verdict.message

    def test_missing_cost_field_treated_as_zero(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({}, {"max_cost_per_action": 0.10})
        assert verdict.passed

    def test_custom_cost_field(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate(
            {"estimated_cost": 0.50},
            {"cost_field": "estimated_cost", "max_cost_per_action": 0.10},
        )
        assert not verdict.passed

    def test_aggregate_cost_accumulates(self) -> None:
        rule = CostLimitRule()
        rule.evaluate({"cost": 2.0}, {"max_cost_aggregate": 5.0})
        rule.evaluate({"cost": 2.0}, {"max_cost_aggregate": 5.0})
        assert rule.aggregate_cost == 4.0

    def test_fails_when_projected_aggregate_exceeds_limit(self) -> None:
        rule = CostLimitRule()
        rule.evaluate({"cost": 4.0}, {"max_cost_aggregate": 5.0})
        verdict = rule.evaluate({"cost": 2.0}, {"max_cost_aggregate": 5.0})
        assert not verdict.passed
        assert "aggregate limit" in verdict.message

    def test_aggregate_not_incremented_on_per_action_failure(self) -> None:
        rule = CostLimitRule()
        rule.evaluate({"cost": 1.0}, {"max_cost_per_action": 0.5, "max_cost_aggregate": 10.0})
        assert rule.aggregate_cost == 0.0

    def test_reset_aggregate(self) -> None:
        rule = CostLimitRule()
        rule.evaluate({"cost": 3.0}, {})
        rule.reset_aggregate()
        assert rule.aggregate_cost == 0.0

    def test_validate_config_invalid_value_returns_error(self) -> None:
        rule = CostLimitRule()
        errors = rule.validate_config({"max_cost_per_action": "not-a-number"})
        assert errors

    def test_validate_config_negative_value_returns_error(self) -> None:
        rule = CostLimitRule()
        errors = rule.validate_config({"max_cost_aggregate": -1.0})
        assert errors

    def test_validate_config_valid_returns_empty(self) -> None:
        rule = CostLimitRule()
        errors = rule.validate_config({"max_cost_per_action": 1.0, "max_cost_aggregate": 10.0})
        assert errors == []

    def test_validate_config_empty_config_valid(self) -> None:
        rule = CostLimitRule()
        assert rule.validate_config({}) == []

    def test_rule_name(self) -> None:
        assert CostLimitRule.name == "cost_limit"

    def test_zero_cost_always_passes_with_limits(self) -> None:
        rule = CostLimitRule()
        verdict = rule.evaluate({"cost": 0}, {"max_cost_per_action": 0.01, "max_cost_aggregate": 0.01})
        assert verdict.passed


# ---------------------------------------------------------------------------
# KeywordBlockRule
# ---------------------------------------------------------------------------


class TestKeywordBlockRule:
    def test_passes_with_no_keywords_configured(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate({"text": "hello world"}, {"keywords": []})
        assert verdict.passed

    def test_fails_when_keyword_found_case_insensitive(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"query": "DROP TABLE users"},
            {"keywords": ["drop table"]},
        )
        assert not verdict.passed
        assert "drop table" in verdict.message.lower()

    def test_passes_when_no_keyword_match(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"query": "select * from users"},
            {"keywords": ["drop table", "rm -rf"]},
        )
        assert verdict.passed

    def test_case_sensitive_match(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"text": "DROP TABLE"},
            {"keywords": ["drop table"], "case_sensitive": True},
        )
        assert verdict.passed  # case doesn't match

    def test_case_sensitive_exact_match(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"text": "drop table"},
            {"keywords": ["drop table"], "case_sensitive": True},
        )
        assert not verdict.passed

    def test_whole_word_match(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"text": "delete files"},
            {"keywords": ["delete"], "match_whole_word": True},
        )
        assert not verdict.passed

    def test_whole_word_no_partial_match(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"text": "undeleted records"},
            {"keywords": ["delete"], "match_whole_word": True},
        )
        assert verdict.passed

    def test_nested_dict_values_scanned(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"outer": {"inner": "rm -rf /"}},
            {"keywords": ["rm -rf"]},
        )
        assert not verdict.passed

    def test_list_values_scanned(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"items": ["safe", "DROP TABLE users"]},
            {"keywords": ["drop table"]},
        )
        assert not verdict.passed

    def test_non_string_keywords_config_converted(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"text": "foo"},
            {"keywords": "foo"},  # non-list → converted to list
        )
        assert not verdict.passed

    def test_multiple_matches_reported(self) -> None:
        rule = KeywordBlockRule()
        verdict = rule.evaluate(
            {"q": "delete all and drop table"},
            {"keywords": ["delete all", "drop table"]},
        )
        assert not verdict.passed

    def test_validate_config_no_keywords_key(self) -> None:
        rule = KeywordBlockRule()
        errors = rule.validate_config({})
        assert errors

    def test_validate_config_non_list_keywords(self) -> None:
        rule = KeywordBlockRule()
        errors = rule.validate_config({"keywords": "single"})
        assert errors

    def test_validate_config_empty_list(self) -> None:
        rule = KeywordBlockRule()
        errors = rule.validate_config({"keywords": []})
        assert errors

    def test_validate_config_valid(self) -> None:
        rule = KeywordBlockRule()
        errors = rule.validate_config({"keywords": ["foo", "bar"]})
        assert errors == []

    def test_rule_name(self) -> None:
        assert KeywordBlockRule.name == "keyword_block"


# ---------------------------------------------------------------------------
# _extract_strings and _matches helpers
# ---------------------------------------------------------------------------


class TestExtractStrings:
    def test_flat_dict(self) -> None:
        result = _extract_strings({"key": "value", "num": 42})
        assert ("key", "value") in result

    def test_nested_dict(self) -> None:
        result = _extract_strings({"outer": {"inner": "deep"}})
        paths = [path for path, _ in result]
        assert any("inner" in p for p in paths)

    def test_list_values(self) -> None:
        result = _extract_strings({"items": ["a", "b"]})
        values = [v for _, v in result]
        assert "a" in values
        assert "b" in values

    def test_nested_list_of_dicts(self) -> None:
        result = _extract_strings({"records": [{"name": "Alice"}]})
        values = [v for _, v in result]
        assert "Alice" in values


class TestExtractStringsFromList:
    def test_extracts_nested_list(self) -> None:
        result = _extract_strings_from_list([["x", "y"]], "root")
        values = [v for _, v in result]
        assert "x" in values

    def test_extracts_dict_in_list(self) -> None:
        result = _extract_strings_from_list([{"k": "v"}], "root")
        values = [v for _, v in result]
        assert "v" in values


class TestMatches:
    def test_case_insensitive_match(self) -> None:
        assert _matches("Hello World", "hello", case_sensitive=False, whole_word=False)

    def test_case_sensitive_no_match(self) -> None:
        assert not _matches("Hello", "hello", case_sensitive=True, whole_word=False)

    def test_whole_word_match(self) -> None:
        assert _matches("delete the file", "delete", case_sensitive=False, whole_word=True)

    def test_whole_word_no_partial(self) -> None:
        assert not _matches("undelete", "delete", case_sensitive=False, whole_word=True)

    def test_substring_match_default(self) -> None:
        assert _matches("abcdef", "cde", case_sensitive=False, whole_word=False)

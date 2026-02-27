"""Tests for NlCompiler."""
from __future__ import annotations

import pytest

from agent_gov.authoring.nl_compiler import (
    CompiledPolicy,
    CompiledRule,
    NlCompiler,
    NlCompilerError,
    ParsedStatement,
    _extract_action,
    _extract_cost_limit,
    _extract_keywords_list,
    _extract_severity,
    _extract_subject,
    _extract_target,
    _make_rule_name,
)


class TestExtractHelpers:
    def test_extract_action_block(self) -> None:
        assert _extract_action("block all pii") == "block"

    def test_extract_action_deny(self) -> None:
        assert _extract_action("deny unauthorized access") == "block"

    def test_extract_action_allow(self) -> None:
        assert _extract_action("allow only admin role") == "allow"

    def test_extract_action_audit(self) -> None:
        assert _extract_action("audit all tool calls") == "audit"

    def test_extract_action_rate_limit(self) -> None:
        assert _extract_action("rate limit requests") == "rate_limit"

    def test_extract_action_throttle(self) -> None:
        assert _extract_action("throttle api calls") == "rate_limit"

    def test_extract_action_default_is_block(self) -> None:
        assert _extract_action("something unknown") == "block"

    def test_extract_subject_pii(self) -> None:
        subject, rule_type, _ = _extract_subject("block pii in responses")
        assert subject == "pii"
        assert rule_type == "pii_check"

    def test_extract_subject_personal_information(self) -> None:
        subject, rule_type, _ = _extract_subject("block personal information")
        assert subject == "pii"

    def test_extract_subject_cost(self) -> None:
        subject, rule_type, _ = _extract_subject("limit cost to $5.00")
        assert subject == "cost"
        assert rule_type == "cost_limit"

    def test_extract_subject_keywords(self) -> None:
        subject, rule_type, _ = _extract_subject("block keywords in requests")
        assert subject == "keywords"
        assert rule_type == "keyword_block"

    def test_extract_subject_role(self) -> None:
        subject, rule_type, _ = _extract_subject("deny unauthorized role access")
        assert subject == "role"
        assert rule_type == "role_check"

    def test_extract_subject_unknown_returns_empty(self) -> None:
        subject, rule_type, _ = _extract_subject("do something weird")
        assert subject == ""
        assert rule_type == ""

    def test_extract_target_response(self) -> None:
        assert _extract_target("block pii in responses") == "response"

    def test_extract_target_request(self) -> None:
        assert _extract_target("block keywords in requests") == "request"

    def test_extract_target_tool_call(self) -> None:
        assert _extract_target("audit all tool calls") == "tool_call"

    def test_extract_target_default_any(self) -> None:
        assert _extract_target("block something") == "any"

    def test_extract_severity_high(self) -> None:
        assert _extract_severity("block pii with high severity") == "high"

    def test_extract_severity_critical(self) -> None:
        assert _extract_severity("block critical content") == "critical"

    def test_extract_severity_default_medium(self) -> None:
        assert _extract_severity("block pii") == "medium"

    def test_extract_cost_limit_with_dollar(self) -> None:
        assert _extract_cost_limit("limit cost to $5.00") == pytest.approx(5.0)

    def test_extract_cost_limit_without_dollar(self) -> None:
        assert _extract_cost_limit("max cost 2.50") == pytest.approx(2.5)

    def test_extract_cost_limit_none_when_absent(self) -> None:
        assert _extract_cost_limit("block pii") is None

    def test_extract_keywords_list(self) -> None:
        words = _extract_keywords_list('block keywords "spam", "scam"')
        assert words == ["spam", "scam"]

    def test_extract_keywords_list_empty(self) -> None:
        assert _extract_keywords_list("block keywords in requests") == []

    def test_make_rule_name(self) -> None:
        name = _make_rule_name("block", "pii", "response")
        assert name == "block-pii-response"

    def test_make_rule_name_any_target_omitted(self) -> None:
        name = _make_rule_name("audit", "role", "any")
        assert name == "audit-role"


class TestNlCompilerParseStatement:
    def setup_method(self) -> None:
        self.compiler = NlCompiler()

    def test_parse_pii_block(self) -> None:
        stmt = self.compiler.parse_statement("Block PII in responses")
        assert isinstance(stmt, ParsedStatement)
        assert stmt.action == "block"
        assert stmt.subject == "pii"
        assert stmt.target == "response"
        assert stmt.confidence > 0.5

    def test_parse_audit_tool_calls(self) -> None:
        stmt = self.compiler.parse_statement("Audit all tool calls")
        assert stmt.action == "audit"
        assert stmt.subject == ""  # "tool" maps to target, not subject

    def test_parse_unknown_subject_low_confidence(self) -> None:
        stmt = self.compiler.parse_statement("Do something obscure")
        assert stmt.confidence < 0.5

    def test_parse_strict_mode_raises_on_unknown(self) -> None:
        strict_compiler = NlCompiler(strict=True)
        with pytest.raises(NlCompilerError):
            strict_compiler.parse_statement("Do something obscure")


class TestNlCompilerCompileStatement:
    def setup_method(self) -> None:
        self.compiler = NlCompiler()

    def test_compile_block_pii_returns_rule(self) -> None:
        rule = self.compiler.compile_statement("Block PII in responses")
        assert isinstance(rule, CompiledRule)
        assert rule.rule_type == "pii_check"
        assert rule.action == "block"
        assert rule.target == "response"

    def test_compile_audit_cost(self) -> None:
        rule = self.compiler.compile_statement("Audit cost usage")
        assert rule is not None
        assert rule.rule_type == "cost_limit"
        assert rule.action == "audit"

    def test_compile_unknown_subject_returns_none(self) -> None:
        rule = self.compiler.compile_statement("Do something weird")
        assert rule is None

    def test_compile_strict_raises_on_unknown(self) -> None:
        strict = NlCompiler(strict=True)
        with pytest.raises(NlCompilerError):
            strict.compile_statement("Do something weird")

    def test_compile_cost_with_dollar_amount(self) -> None:
        rule = self.compiler.compile_statement("Limit cost to $3.50 per call")
        assert rule is not None
        assert rule.params.get("max_cost") == pytest.approx(3.5)

    def test_compile_keywords_with_quoted_words(self) -> None:
        rule = self.compiler.compile_statement('Block keywords "spam", "scam" in responses')
        assert rule is not None
        assert "spam" in rule.params.get("keywords", [])
        assert "scam" in rule.params.get("keywords", [])

    def test_compile_rule_has_severity(self) -> None:
        rule = self.compiler.compile_statement("Block PII with high severity")
        assert rule is not None
        assert rule.severity == "high"

    def test_compile_rule_name_is_slug(self) -> None:
        rule = self.compiler.compile_statement("Block PII in responses")
        assert rule is not None
        assert " " not in rule.name


class TestNlCompilerCompile:
    def setup_method(self) -> None:
        self.compiler = NlCompiler()

    def test_compile_returns_compiled_policy(self) -> None:
        policy = self.compiler.compile("Block PII in responses")
        assert isinstance(policy, CompiledPolicy)
        assert len(policy.rules) == 1

    def test_compile_policy_name_default(self) -> None:
        policy = self.compiler.compile("Block PII in responses")
        assert policy.name == "generated-policy"

    def test_compile_policy_name_override(self) -> None:
        policy = self.compiler.compile("Block PII in responses", policy_name="my-policy")
        assert policy.name == "my-policy"

    def test_compile_unknown_adds_warning(self) -> None:
        policy = self.compiler.compile("Do something obscure")
        assert len(policy.rules) == 0
        assert len(policy.warnings) > 0

    def test_compile_to_yaml_contains_rules(self) -> None:
        policy = self.compiler.compile("Block PII in responses")
        yaml_text = policy.to_yaml()
        assert "pii_check" in yaml_text
        assert "rules:" in yaml_text

    def test_compile_to_dict_structure(self) -> None:
        policy = self.compiler.compile("Audit cost usage")
        d = policy.to_dict()
        assert "name" in d
        assert "rules" in d
        assert isinstance(d["rules"], list)


class TestNlCompilerCompileMany:
    def setup_method(self) -> None:
        self.compiler = NlCompiler()

    def test_compile_many_multiple_rules(self) -> None:
        policy = self.compiler.compile_many([
            "Block PII in responses",
            "Audit cost usage",
            "Rate limit requests",
        ])
        assert len(policy.rules) >= 2

    def test_compile_many_skips_unknown_statements(self) -> None:
        policy = self.compiler.compile_many([
            "Block PII in responses",
            "Something completely unknown",
        ])
        assert len(policy.rules) == 1
        assert len(policy.warnings) == 1

    def test_compile_many_deduplicates_rule_names(self) -> None:
        policy = self.compiler.compile_many([
            "Block PII in responses",
            "Block PII in responses",
        ])
        names = [r.name for r in policy.rules]
        assert len(names) == len(set(names))

    def test_compile_many_policy_name_override(self) -> None:
        policy = self.compiler.compile_many(
            ["Block PII in responses"],
            policy_name="custom-policy",
        )
        assert policy.name == "custom-policy"


class TestNlCompilerCompileTextBlock:
    def setup_method(self) -> None:
        self.compiler = NlCompiler()

    def test_compile_text_block_skips_empty_lines(self) -> None:
        text = """
Block PII in responses

Audit cost usage
"""
        policy = self.compiler.compile_text_block(text)
        assert len(policy.rules) >= 1

    def test_compile_text_block_skips_comments(self) -> None:
        text = """
# This is a comment
Block PII in responses
# Another comment
"""
        policy = self.compiler.compile_text_block(text)
        assert len(policy.rules) == 1

    def test_compile_text_block_with_policy_name(self) -> None:
        policy = self.compiler.compile_text_block(
            "Block PII in responses",
            policy_name="text-block-policy",
        )
        assert policy.name == "text-block-policy"

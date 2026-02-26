"""Unit tests for agent_gov.policy.result.EvaluationReport.

Covers computed properties (failed_verdicts, passed_verdicts, violation_count,
highest_severity), to_dict serialisation, and summary formatting.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_gov.policy.result import EvaluationReport
from agent_gov.policy.rule import RuleVerdict


def _make_verdict(
    *,
    rule_name: str = "rule",
    passed: bool = True,
    severity: str = "medium",
    message: str = "",
) -> RuleVerdict:
    return RuleVerdict(rule_name=rule_name, passed=passed, severity=severity, message=message)


class TestEvaluationReportDefaults:
    def test_construction_with_required_fields(self) -> None:
        report = EvaluationReport(policy_name="my-policy", action={"type": "search"})
        assert report.policy_name == "my-policy"
        assert report.action == {"type": "search"}

    def test_default_verdicts_is_empty(self) -> None:
        report = EvaluationReport(policy_name="p", action={})
        assert report.verdicts == []

    def test_default_passed_is_true(self) -> None:
        report = EvaluationReport(policy_name="p", action={})
        assert report.passed is True

    def test_timestamp_is_utc(self) -> None:
        report = EvaluationReport(policy_name="p", action={})
        assert report.timestamp.tzinfo is not None


class TestEvaluationReportProperties:
    def test_failed_verdicts_filters_correctly(self) -> None:
        pass_verdict = _make_verdict(rule_name="r1", passed=True)
        fail_verdict = _make_verdict(rule_name="r2", passed=False)
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[pass_verdict, fail_verdict],
        )
        assert len(report.failed_verdicts) == 1
        assert report.failed_verdicts[0].rule_name == "r2"

    def test_passed_verdicts_filters_correctly(self) -> None:
        pass_verdict = _make_verdict(rule_name="r1", passed=True)
        fail_verdict = _make_verdict(rule_name="r2", passed=False)
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[pass_verdict, fail_verdict],
        )
        assert len(report.passed_verdicts) == 1
        assert report.passed_verdicts[0].rule_name == "r1"

    def test_violation_count_zero_when_all_pass(self) -> None:
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[_make_verdict(passed=True)],
        )
        assert report.violation_count == 0

    def test_violation_count_matches_failures(self) -> None:
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[
                _make_verdict(passed=False),
                _make_verdict(passed=False),
                _make_verdict(passed=True),
            ],
        )
        assert report.violation_count == 2

    def test_highest_severity_none_when_no_failures(self) -> None:
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[_make_verdict(passed=True, severity="critical")],
        )
        assert report.highest_severity == "none"

    def test_highest_severity_from_single_failure(self) -> None:
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[_make_verdict(passed=False, severity="high")],
        )
        assert report.highest_severity == "high"

    def test_highest_severity_picks_maximum(self) -> None:
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[
                _make_verdict(passed=False, severity="low"),
                _make_verdict(passed=False, severity="critical"),
                _make_verdict(passed=False, severity="medium"),
            ],
        )
        assert report.highest_severity == "critical"

    def test_highest_severity_none_when_empty_verdicts(self) -> None:
        report = EvaluationReport(policy_name="p", action={})
        assert report.highest_severity == "none"


class TestEvaluationReportToDict:
    def test_to_dict_contains_required_keys(self) -> None:
        report = EvaluationReport(policy_name="p", action={"type": "test"})
        result = report.to_dict()
        expected_keys = {
            "policy_name", "action", "passed", "timestamp",
            "violation_count", "highest_severity", "verdicts",
        }
        assert expected_keys.issubset(result.keys())

    def test_to_dict_policy_name(self) -> None:
        report = EvaluationReport(policy_name="my-policy", action={})
        assert report.to_dict()["policy_name"] == "my-policy"

    def test_to_dict_passed_reflects_state(self) -> None:
        report = EvaluationReport(policy_name="p", action={}, passed=False)
        assert report.to_dict()["passed"] is False

    def test_to_dict_timestamp_is_isoformat_string(self) -> None:
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        report = EvaluationReport(policy_name="p", action={}, timestamp=ts)
        result = report.to_dict()
        assert "2024-06-01" in result["timestamp"]  # type: ignore[operator]

    def test_to_dict_verdicts_is_list_of_dicts(self) -> None:
        verdict = _make_verdict(rule_name="r", passed=False)
        report = EvaluationReport(policy_name="p", action={}, verdicts=[verdict])
        result = report.to_dict()
        assert isinstance(result["verdicts"], list)
        assert isinstance(result["verdicts"][0], dict)  # type: ignore[index]


class TestEvaluationReportSummary:
    def test_summary_pass_contains_pass(self) -> None:
        report = EvaluationReport(policy_name="my-policy", action={}, passed=True)
        assert "PASS" in report.summary()

    def test_summary_fail_contains_fail(self) -> None:
        report = EvaluationReport(policy_name="my-policy", action={}, passed=False)
        assert "FAIL" in report.summary()

    def test_summary_contains_policy_name(self) -> None:
        report = EvaluationReport(policy_name="my-special-policy", action={})
        assert "my-special-policy" in report.summary()

    def test_summary_contains_violation_count(self) -> None:
        report = EvaluationReport(
            policy_name="p",
            action={},
            verdicts=[_make_verdict(passed=False)],
            passed=False,
        )
        assert "violations=1" in report.summary()

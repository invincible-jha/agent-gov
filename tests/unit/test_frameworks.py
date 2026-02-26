"""Tests for compliance framework implementations and base classes."""
from __future__ import annotations

import pytest

from agent_gov.frameworks.base import (
    ChecklistItem,
    CheckResult,
    ComplianceFramework,
    FrameworkReport,
)
from agent_gov.frameworks.eu_ai_act import EuAiActFramework, _resolve_evidence
from agent_gov.frameworks.gdpr import GdprFramework
from agent_gov.frameworks.hipaa import HipaaFramework
from agent_gov.frameworks.soc2 import Soc2Framework


# ---------------------------------------------------------------------------
# FrameworkReport
# ---------------------------------------------------------------------------


def _make_item(id: str = "C1", name: str = "Item") -> ChecklistItem:
    return ChecklistItem(id=id, name=name, description="desc", category="test")


def _make_result(status: str = "pass", item_id: str = "C1") -> CheckResult:
    return CheckResult(item=_make_item(item_id), status=status)


class TestFrameworkReport:
    def test_score_all_pass(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("pass"), _make_result("pass")],
        )
        assert report.score == 1.0

    def test_score_all_fail(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("fail"), _make_result("fail")],
        )
        assert report.score == 0.0

    def test_score_mixed(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("pass"), _make_result("fail"), _make_result("unknown")],
        )
        assert report.score == pytest.approx(1 / 3)

    def test_score_empty_is_zero(self) -> None:
        report = FrameworkReport(framework="test", results=[])
        assert report.score == 0.0

    def test_score_percent(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("pass"), _make_result("fail")],
        )
        assert report.score_percent == pytest.approx(50.0)

    def test_passed_count(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("pass"), _make_result("pass"), _make_result("fail")],
        )
        assert report.passed_count == 2

    def test_failed_count(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("fail"), _make_result("fail"), _make_result("unknown")],
        )
        assert report.failed_count == 2

    def test_unknown_count(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("unknown"), _make_result("pass")],
        )
        assert report.unknown_count == 1

    def test_to_dict_keys(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[_make_result("pass")],
        )
        d = report.to_dict()
        assert "framework" in d
        assert "score" in d
        assert "score_percent" in d
        assert "passed" in d
        assert "failed" in d
        assert "unknown" in d
        assert "results" in d

    def test_to_dict_results_structure(self) -> None:
        report = FrameworkReport(
            framework="test",
            results=[CheckResult(item=_make_item("X1"), status="pass", evidence="evidence text")],
        )
        d = report.to_dict()
        result_dict = d["results"][0]  # type: ignore[index]
        assert result_dict["id"] == "X1"
        assert result_dict["status"] == "pass"
        assert result_dict["evidence"] == "evidence text"


# ---------------------------------------------------------------------------
# EuAiActFramework
# ---------------------------------------------------------------------------


class TestEuAiActFramework:
    def test_checklist_has_eight_items(self) -> None:
        fw = EuAiActFramework()
        assert len(fw.checklist()) == 8

    def test_checklist_ids(self) -> None:
        fw = EuAiActFramework()
        ids = {item.id for item in fw.checklist()}
        assert ids == {"A6", "A9", "A10", "A13", "A14", "A15", "A52", "A60"}

    def test_run_check_all_pass(self) -> None:
        fw = EuAiActFramework()
        evidence = {item.id: {"status": "pass", "evidence": "ok"} for item in fw.checklist()}
        report = fw.run_check(evidence)
        assert report.passed_count == 8
        assert report.failed_count == 0

    def test_run_check_no_evidence_gives_unknown(self) -> None:
        fw = EuAiActFramework()
        report = fw.run_check({})
        assert report.unknown_count == 8

    def test_run_check_partial_evidence(self) -> None:
        fw = EuAiActFramework()
        report = fw.run_check({
            "A6": {"status": "pass"},
            "A9": {"status": "fail"},
        })
        assert report.passed_count == 1
        assert report.failed_count == 1
        assert report.unknown_count == 6

    def test_run_check_truthy_scalar(self) -> None:
        fw = EuAiActFramework()
        report = fw.run_check({"A6": True, "A9": False})
        a6 = next(r for r in report.results if r.item.id == "A6")
        a9 = next(r for r in report.results if r.item.id == "A9")
        assert a6.status == "pass"
        assert a9.status == "fail"

    def test_framework_name_is_eu_ai_act(self) -> None:
        assert EuAiActFramework.name == "eu-ai-act"

    def test_report_framework_name(self) -> None:
        fw = EuAiActFramework()
        report = fw.run_check({})
        assert report.framework == "eu-ai-act"

    def test_repr(self) -> None:
        fw = EuAiActFramework()
        assert "eu-ai-act" in repr(fw)


class TestResolveEvidence:
    def test_none_returns_unknown(self) -> None:
        status, _ = _resolve_evidence(None)
        assert status == "unknown"

    def test_truthy_scalar_returns_pass(self) -> None:
        status, _ = _resolve_evidence(True)
        assert status == "pass"

    def test_falsy_scalar_returns_fail(self) -> None:
        status, _ = _resolve_evidence(False)
        assert status == "fail"

    def test_dict_with_pass_status(self) -> None:
        status, evidence = _resolve_evidence({"status": "pass", "evidence": "done"})
        assert status == "pass"
        assert evidence == "done"

    def test_dict_with_invalid_status_defaults_to_unknown(self) -> None:
        status, _ = _resolve_evidence({"status": "maybe"})
        assert status == "unknown"


# ---------------------------------------------------------------------------
# GDPR, HIPAA, SOC2 framework smoke tests
# ---------------------------------------------------------------------------


class TestGdprFramework:
    def test_has_items(self) -> None:
        fw = GdprFramework()
        assert len(fw.checklist()) > 0

    def test_run_check_no_evidence(self) -> None:
        fw = GdprFramework()
        report = fw.run_check({})
        assert report.framework == GdprFramework.name
        assert all(r.status in ("unknown", "fail", "pass") for r in report.results)

    def test_run_check_all_pass(self) -> None:
        fw = GdprFramework()
        evidence = {item.id: {"status": "pass"} for item in fw.checklist()}
        report = fw.run_check(evidence)
        assert report.score == pytest.approx(1.0)

    def test_to_dict_serialisable(self) -> None:
        fw = GdprFramework()
        report = fw.run_check({})
        d = report.to_dict()
        assert isinstance(d["score_percent"], float)


class TestHipaaFramework:
    def test_has_items(self) -> None:
        fw = HipaaFramework()
        assert len(fw.checklist()) > 0

    def test_run_check_returns_report(self) -> None:
        fw = HipaaFramework()
        report = fw.run_check({})
        assert report.framework == HipaaFramework.name

    def test_run_check_all_pass(self) -> None:
        fw = HipaaFramework()
        evidence = {item.id: {"status": "pass"} for item in fw.checklist()}
        report = fw.run_check(evidence)
        assert report.score == pytest.approx(1.0)


class TestSoc2Framework:
    def test_has_items(self) -> None:
        fw = Soc2Framework()
        assert len(fw.checklist()) > 0

    def test_run_check_returns_report(self) -> None:
        fw = Soc2Framework()
        report = fw.run_check({})
        assert report.framework == Soc2Framework.name

    def test_run_check_all_pass(self) -> None:
        fw = Soc2Framework()
        evidence = {item.id: {"status": "pass"} for item in fw.checklist()}
        report = fw.run_check(evidence)
        assert report.score == pytest.approx(1.0)

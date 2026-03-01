"""Tests for expanded EU AI Act, ISO 42001, NIST AI RMF, and GapAnalyzer.

Test coverage:
- EU AI Act: 40+ items, full pass, partial pass, full fail, unique IDs (15 tests)
- ISO 42001: 30+ items, full pass, partial pass, full fail, unique IDs (15 tests)
- NIST AI RMF: 25+ items, full pass, partial pass, full fail, unique IDs (15 tests)
- GapAnalyzer: overlap detection, unique requirements, remediation dedup,
               coverage score, and report structure (15 tests)
Total: 60 tests
"""
from __future__ import annotations

import pytest

from agent_gov.frameworks.eu_ai_act import EuAiActFramework
from agent_gov.frameworks.gap_analyzer import GapAnalysisReport, GapAnalyzer, OverlapGroup, RemediationItem
from agent_gov.frameworks.iso_42001 import Iso42001Framework
from agent_gov.frameworks.nist_ai_rmf import NistAiRmfFramework


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_pass_evidence(framework: EuAiActFramework | Iso42001Framework | NistAiRmfFramework) -> dict[str, object]:
    return {item.id: {"status": "pass", "evidence": "verified"} for item in framework.checklist()}


def _all_fail_evidence(framework: EuAiActFramework | Iso42001Framework | NistAiRmfFramework) -> dict[str, object]:
    return {item.id: {"status": "fail", "evidence": "not implemented"} for item in framework.checklist()}


# ===========================================================================
# EU AI Act — 15 tests
# ===========================================================================


class TestEuAiActExpanded:
    """Tests for the expanded EuAiActFramework (40+ items)."""

    def test_checklist_has_at_least_40_items(self) -> None:
        framework = EuAiActFramework()
        assert len(framework.checklist()) >= 40

    def test_checklist_ids_are_unique(self) -> None:
        framework = EuAiActFramework()
        all_ids = [item.id for item in framework.checklist()]
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found in EU AI Act checklist"

    def test_checklist_contains_prohibited_practices(self) -> None:
        framework = EuAiActFramework()
        all_ids = {item.id for item in framework.checklist()}
        assert "A5_1" in all_ids
        assert "A5_2" in all_ids
        assert "A5_3" in all_ids
        assert "A5_4" in all_ids

    def test_checklist_contains_high_risk_articles(self) -> None:
        framework = EuAiActFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"A6", "A7", "A8", "A9", "A10", "A11", "A12", "A13", "A14", "A15"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_provider_deployer_obligations(self) -> None:
        framework = EuAiActFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"A16", "A17", "A22", "A26", "A27", "A29"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_transparency_articles(self) -> None:
        framework = EuAiActFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"A50", "A52", "A53", "A55", "A56"}
        assert required_ids.issubset(all_ids)

    def test_all_items_have_non_empty_name(self) -> None:
        framework = EuAiActFramework()
        for item in framework.checklist():
            assert item.name, f"Item {item.id} has empty name"

    def test_all_items_have_non_empty_description(self) -> None:
        framework = EuAiActFramework()
        for item in framework.checklist():
            assert item.description, f"Item {item.id} has empty description"

    def test_all_items_have_category(self) -> None:
        framework = EuAiActFramework()
        for item in framework.checklist():
            assert item.category, f"Item {item.id} has empty category"

    def test_full_pass(self) -> None:
        framework = EuAiActFramework()
        report = framework.run_check(_all_pass_evidence(framework))
        assert report.score == pytest.approx(1.0)
        assert report.failed_count == 0
        assert report.unknown_count == 0

    def test_full_fail(self) -> None:
        framework = EuAiActFramework()
        report = framework.run_check(_all_fail_evidence(framework))
        assert report.score == pytest.approx(0.0)
        assert report.passed_count == 0
        assert report.unknown_count == 0

    def test_no_evidence_all_unknown(self) -> None:
        framework = EuAiActFramework()
        report = framework.run_check({})
        checklist_count = len(framework.checklist())
        assert report.unknown_count == checklist_count

    def test_partial_pass(self) -> None:
        framework = EuAiActFramework()
        partial_evidence: dict[str, object] = {
            "A6": {"status": "pass"},
            "A9": {"status": "pass"},
            "A10": {"status": "fail"},
        }
        report = framework.run_check(partial_evidence)
        assert report.passed_count == 2
        assert report.failed_count == 1
        total = len(framework.checklist())
        assert report.unknown_count == total - 3

    def test_report_framework_name(self) -> None:
        framework = EuAiActFramework()
        report = framework.run_check({})
        assert report.framework == "eu-ai-act"

    def test_result_count_matches_checklist(self) -> None:
        framework = EuAiActFramework()
        report = framework.run_check({})
        assert len(report.results) == len(framework.checklist())


# ===========================================================================
# ISO 42001 — 15 tests
# ===========================================================================


class TestIso42001Framework:
    """Tests for the Iso42001Framework (30+ items)."""

    def test_checklist_has_at_least_30_items(self) -> None:
        framework = Iso42001Framework()
        assert len(framework.checklist()) >= 30

    def test_checklist_ids_are_unique(self) -> None:
        framework = Iso42001Framework()
        all_ids = [item.id for item in framework.checklist()]
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found in ISO 42001 checklist"

    def test_checklist_contains_clause_4_items(self) -> None:
        framework = Iso42001Framework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"ISO42001_C4_1", "ISO42001_C4_2", "ISO42001_C4_3", "ISO42001_C4_4"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_clause_5_items(self) -> None:
        framework = Iso42001Framework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"ISO42001_C5_1", "ISO42001_C5_2", "ISO42001_C5_3", "ISO42001_C5_4"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_clause_6_items(self) -> None:
        framework = Iso42001Framework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"ISO42001_C6_1", "ISO42001_C6_2", "ISO42001_C6_3", "ISO42001_C6_4"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_annex_a_items(self) -> None:
        framework = Iso42001Framework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"ISO42001_A5", "ISO42001_A6", "ISO42001_A9", "ISO42001_A10"}
        assert required_ids.issubset(all_ids)

    def test_all_items_have_non_empty_name(self) -> None:
        framework = Iso42001Framework()
        for item in framework.checklist():
            assert item.name, f"Item {item.id} has empty name"

    def test_all_items_have_non_empty_description(self) -> None:
        framework = Iso42001Framework()
        for item in framework.checklist():
            assert item.description, f"Item {item.id} has empty description"

    def test_all_items_have_category(self) -> None:
        framework = Iso42001Framework()
        for item in framework.checklist():
            assert item.category, f"Item {item.id} has empty category"

    def test_full_pass(self) -> None:
        framework = Iso42001Framework()
        report = framework.run_check(_all_pass_evidence(framework))
        assert report.score == pytest.approx(1.0)
        assert report.failed_count == 0
        assert report.unknown_count == 0

    def test_full_fail(self) -> None:
        framework = Iso42001Framework()
        report = framework.run_check(_all_fail_evidence(framework))
        assert report.score == pytest.approx(0.0)
        assert report.passed_count == 0
        assert report.unknown_count == 0

    def test_no_evidence_all_unknown(self) -> None:
        framework = Iso42001Framework()
        report = framework.run_check({})
        assert report.unknown_count == len(framework.checklist())

    def test_partial_pass(self) -> None:
        framework = Iso42001Framework()
        partial_evidence: dict[str, object] = {
            "ISO42001_C4_1": {"status": "pass"},
            "ISO42001_C5_1": {"status": "pass"},
            "ISO42001_C6_1": {"status": "fail"},
        }
        report = framework.run_check(partial_evidence)
        assert report.passed_count == 2
        assert report.failed_count == 1

    def test_report_framework_name(self) -> None:
        framework = Iso42001Framework()
        report = framework.run_check({})
        assert report.framework == "iso-42001"

    def test_result_count_matches_checklist(self) -> None:
        framework = Iso42001Framework()
        report = framework.run_check({})
        assert len(report.results) == len(framework.checklist())


# ===========================================================================
# NIST AI RMF — 15 tests
# ===========================================================================


class TestNistAiRmfFramework:
    """Tests for the NistAiRmfFramework (25+ items)."""

    def test_checklist_has_at_least_25_items(self) -> None:
        framework = NistAiRmfFramework()
        assert len(framework.checklist()) >= 25

    def test_checklist_ids_are_unique(self) -> None:
        framework = NistAiRmfFramework()
        all_ids = [item.id for item in framework.checklist()]
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found in NIST AI RMF checklist"

    def test_checklist_contains_govern_items(self) -> None:
        framework = NistAiRmfFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"NIST_G1", "NIST_G2", "NIST_G3", "NIST_G4", "NIST_G5", "NIST_G6", "NIST_G7"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_map_items(self) -> None:
        framework = NistAiRmfFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"NIST_M1", "NIST_M2", "NIST_M3", "NIST_M4", "NIST_M5"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_measure_items(self) -> None:
        framework = NistAiRmfFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"NIST_ME1", "NIST_ME2", "NIST_ME3", "NIST_ME4", "NIST_ME5", "NIST_ME6", "NIST_ME7"}
        assert required_ids.issubset(all_ids)

    def test_checklist_contains_manage_items(self) -> None:
        framework = NistAiRmfFramework()
        all_ids = {item.id for item in framework.checklist()}
        required_ids = {"NIST_MA1", "NIST_MA2", "NIST_MA3", "NIST_MA4", "NIST_MA5", "NIST_MA6"}
        assert required_ids.issubset(all_ids)

    def test_all_items_have_non_empty_name(self) -> None:
        framework = NistAiRmfFramework()
        for item in framework.checklist():
            assert item.name, f"Item {item.id} has empty name"

    def test_all_items_have_non_empty_description(self) -> None:
        framework = NistAiRmfFramework()
        for item in framework.checklist():
            assert item.description, f"Item {item.id} has empty description"

    def test_all_items_have_category(self) -> None:
        framework = NistAiRmfFramework()
        for item in framework.checklist():
            assert item.category, f"Item {item.id} has empty category"

    def test_full_pass(self) -> None:
        framework = NistAiRmfFramework()
        report = framework.run_check(_all_pass_evidence(framework))
        assert report.score == pytest.approx(1.0)
        assert report.failed_count == 0
        assert report.unknown_count == 0

    def test_full_fail(self) -> None:
        framework = NistAiRmfFramework()
        report = framework.run_check(_all_fail_evidence(framework))
        assert report.score == pytest.approx(0.0)
        assert report.passed_count == 0
        assert report.unknown_count == 0

    def test_no_evidence_all_unknown(self) -> None:
        framework = NistAiRmfFramework()
        report = framework.run_check({})
        assert report.unknown_count == len(framework.checklist())

    def test_partial_pass(self) -> None:
        framework = NistAiRmfFramework()
        partial_evidence: dict[str, object] = {
            "NIST_G1": {"status": "pass"},
            "NIST_G2": {"status": "pass"},
            "NIST_M1": {"status": "fail"},
        }
        report = framework.run_check(partial_evidence)
        assert report.passed_count == 2
        assert report.failed_count == 1

    def test_report_framework_name(self) -> None:
        framework = NistAiRmfFramework()
        report = framework.run_check({})
        assert report.framework == "nist-ai-rmf"

    def test_result_count_matches_checklist(self) -> None:
        framework = NistAiRmfFramework()
        report = framework.run_check({})
        assert len(report.results) == len(framework.checklist())


# ===========================================================================
# GapAnalyzer — 15 tests
# ===========================================================================


class TestGapAnalyzer:
    """Tests for the GapAnalyzer cross-framework gap analysis."""

    def _make_eu_report(self, pass_ids: list[str] | None = None) -> object:
        """Return an EU AI Act report with specified IDs passing, rest failing."""
        framework = EuAiActFramework()
        if pass_ids is None:
            return framework.run_check({})
        evidence: dict[str, object] = {}
        for item in framework.checklist():
            if item.id in pass_ids:
                evidence[item.id] = {"status": "pass"}
            else:
                evidence[item.id] = {"status": "fail"}
        return framework.run_check(evidence)

    def _make_iso_report(self, pass_ids: list[str] | None = None) -> object:
        """Return an ISO 42001 report with specified IDs passing, rest failing."""
        framework = Iso42001Framework()
        if pass_ids is None:
            return framework.run_check({})
        evidence: dict[str, object] = {}
        for item in framework.checklist():
            if item.id in pass_ids:
                evidence[item.id] = {"status": "pass"}
            else:
                evidence[item.id] = {"status": "fail"}
        return framework.run_check(evidence)

    def _make_nist_report(self, pass_ids: list[str] | None = None) -> object:
        """Return a NIST AI RMF report with specified IDs passing, rest failing."""
        framework = NistAiRmfFramework()
        if pass_ids is None:
            return framework.run_check({})
        evidence: dict[str, object] = {}
        for item in framework.checklist():
            if item.id in pass_ids:
                evidence[item.id] = {"status": "pass"}
            else:
                evidence[item.id] = {"status": "fail"}
        return framework.run_check(evidence)

    def test_empty_input_returns_empty_report(self) -> None:
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([])
        assert gap_report.total_requirements == 0
        assert gap_report.coverage_score == 0.0
        assert gap_report.overlap_groups == []
        assert gap_report.unified_remediation == []

    def test_single_framework_no_overlap_groups(self) -> None:
        """A single framework cannot have cross-framework overlaps."""
        framework = EuAiActFramework()
        report = framework.run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([report])
        assert gap_report.overlap_groups == []

    def test_frameworks_analyzed_field_populated(self) -> None:
        eu_report = EuAiActFramework().run_check({})
        iso_report = Iso42001Framework().run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        assert "eu-ai-act" in gap_report.frameworks_analyzed
        assert "iso-42001" in gap_report.frameworks_analyzed

    def test_total_requirements_is_sum_of_both_checklists(self) -> None:
        eu_framework = EuAiActFramework()
        iso_framework = Iso42001Framework()
        eu_report = eu_framework.run_check({})
        iso_report = iso_framework.run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        expected_total = len(eu_framework.checklist()) + len(iso_framework.checklist())
        assert gap_report.total_requirements == expected_total

    def test_overlap_groups_detected_for_eu_and_iso(self) -> None:
        """EU AI Act and ISO 42001 share multiple compliance themes."""
        eu_report = EuAiActFramework().run_check({})
        iso_report = Iso42001Framework().run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        assert len(gap_report.overlap_groups) > 0, "Expected overlap groups between EU AI Act and ISO 42001"

    def test_overlap_groups_have_multiple_frameworks(self) -> None:
        eu_report = EuAiActFramework().run_check({})
        iso_report = Iso42001Framework().run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        for group in gap_report.overlap_groups:
            assert len(group.frameworks) >= 2
            assert len(group.requirement_ids) >= 2

    def test_unique_requirements_keys_match_frameworks(self) -> None:
        eu_report = EuAiActFramework().run_check({})
        iso_report = Iso42001Framework().run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        assert set(gap_report.unique_requirements.keys()) == {"eu-ai-act", "iso-42001"}

    def test_coverage_score_all_pass(self) -> None:
        eu_framework = EuAiActFramework()
        iso_framework = Iso42001Framework()
        eu_report = eu_framework.run_check(_all_pass_evidence(eu_framework))
        iso_report = iso_framework.run_check(_all_pass_evidence(iso_framework))
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        assert gap_report.coverage_score == pytest.approx(1.0)
        assert gap_report.passing_requirements == gap_report.total_requirements

    def test_coverage_score_all_fail(self) -> None:
        eu_framework = EuAiActFramework()
        nist_framework = NistAiRmfFramework()
        eu_report = eu_framework.run_check(_all_fail_evidence(eu_framework))
        nist_report = nist_framework.run_check(_all_fail_evidence(nist_framework))
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, nist_report])
        assert gap_report.coverage_score == pytest.approx(0.0)
        assert gap_report.passing_requirements == 0

    def test_unified_remediation_deduplicates_themes(self) -> None:
        """Remediation list should have one entry per theme, not per failing item."""
        eu_framework = EuAiActFramework()
        iso_framework = Iso42001Framework()
        eu_report = eu_framework.run_check(_all_fail_evidence(eu_framework))
        iso_report = iso_framework.run_check(_all_fail_evidence(iso_framework))
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report])
        themes = [item.theme for item in gap_report.unified_remediation]
        assert len(themes) == len(set(themes)), "Duplicate themes found in unified_remediation"

    def test_unified_remediation_non_empty_when_failures_exist(self) -> None:
        eu_framework = EuAiActFramework()
        eu_report = eu_framework.run_check(_all_fail_evidence(eu_framework))
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report])
        assert len(gap_report.unified_remediation) > 0

    def test_unified_remediation_empty_when_all_pass(self) -> None:
        eu_framework = EuAiActFramework()
        eu_report = eu_framework.run_check(_all_pass_evidence(eu_framework))
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report])
        assert gap_report.unified_remediation == []

    def test_remediation_items_have_non_empty_descriptions(self) -> None:
        eu_framework = EuAiActFramework()
        eu_report = eu_framework.run_check(_all_fail_evidence(eu_framework))
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report])
        for remediation_item in gap_report.unified_remediation:
            assert remediation_item.action_description, (
                f"Empty action_description for theme {remediation_item.theme}"
            )

    def test_three_framework_analysis(self) -> None:
        """Three-framework analysis produces a valid report."""
        eu_framework = EuAiActFramework()
        iso_framework = Iso42001Framework()
        nist_framework = NistAiRmfFramework()
        eu_report = eu_framework.run_check({})
        iso_report = iso_framework.run_check({})
        nist_report = nist_framework.run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report, iso_report, nist_report])
        expected_total = (
            len(eu_framework.checklist())
            + len(iso_framework.checklist())
            + len(nist_framework.checklist())
        )
        assert gap_report.total_requirements == expected_total
        assert len(gap_report.frameworks_analyzed) == 3

    def test_gap_analysis_report_is_pydantic_model(self) -> None:
        """GapAnalysisReport is a Pydantic model and serialises to dict."""
        eu_report = EuAiActFramework().run_check({})
        analyzer = GapAnalyzer()
        gap_report = analyzer.analyze([eu_report])
        report_dict = gap_report.model_dump()
        assert "frameworks_analyzed" in report_dict
        assert "total_requirements" in report_dict
        assert "coverage_score" in report_dict
        assert "overlap_groups" in report_dict
        assert "unified_remediation" in report_dict

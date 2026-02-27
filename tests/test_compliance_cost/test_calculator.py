"""Tests for agent_gov.compliance_cost.calculator and framework_maps."""
from __future__ import annotations

import pytest

from agent_gov.compliance_cost.calculator import (
    ComparisonReport,
    ComplianceCostCalculator,
    ComplianceRequirement,
    CostReport,
)
from agent_gov.compliance_cost.framework_maps import (
    EU_AI_ACT_REQUIREMENTS,
    GDPR_REQUIREMENTS,
    HIPAA_REQUIREMENTS,
    get_requirements,
    list_frameworks,
)
from agent_gov.compliance_cost.report import CostReportRenderer


# ---------------------------------------------------------------------------
# ComplianceRequirement unit tests
# ---------------------------------------------------------------------------


class TestComplianceRequirement:
    @pytest.fixture()
    def req(self) -> ComplianceRequirement:
        return ComplianceRequirement(
            framework="eu_ai_act",
            requirement_id="A6_risk",
            description="Classify the AI system.",
            automation_level="semi_automated",
            estimated_hours_manual=40.0,
            estimated_hours_automated=8.0,
        )

    def test_frozen(self, req: ComplianceRequirement) -> None:
        with pytest.raises((AttributeError, TypeError)):
            req.framework = "changed"  # type: ignore[misc]

    def test_cost_manual(self, req: ComplianceRequirement) -> None:
        assert req.cost_manual(100.0) == 4000.0

    def test_cost_automated(self, req: ComplianceRequirement) -> None:
        assert req.cost_automated(100.0) == 800.0

    def test_savings(self, req: ComplianceRequirement) -> None:
        assert req.savings(100.0) == 3200.0

    def test_to_dict_keys(self, req: ComplianceRequirement) -> None:
        d = req.to_dict()
        assert "framework" in d
        assert "requirement_id" in d
        assert "description" in d
        assert "automation_level" in d
        assert "estimated_hours_manual" in d
        assert "estimated_hours_automated" in d


# ---------------------------------------------------------------------------
# CostReport unit tests
# ---------------------------------------------------------------------------


class TestCostReport:
    def test_frozen(self) -> None:
        report = CostReport(
            framework="eu_ai_act",
            total_requirements=5,
            automated_count=3,
            semi_automated_count=1,
            manual_count=1,
            total_hours_manual=100.0,
            total_hours_automated=20.0,
            total_cost_manual=15000.0,
            total_cost_with_automation=3000.0,
            savings_percentage=80.0,
            hourly_rate=150.0,
            requirement_details=(),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.framework = "changed"  # type: ignore[misc]

    def test_to_dict_has_keys(self) -> None:
        report = CostReport(
            framework="gdpr",
            total_requirements=10,
            automated_count=4,
            semi_automated_count=4,
            manual_count=2,
            total_hours_manual=300.0,
            total_hours_automated=80.0,
            total_cost_manual=45000.0,
            total_cost_with_automation=12000.0,
            savings_percentage=73.3,
            hourly_rate=150.0,
            requirement_details=(),
        )
        d = report.to_dict()
        assert d["framework"] == "gdpr"
        assert d["total_requirements"] == 10
        assert "savings_percentage" in d

    def test_summary_returns_string(self) -> None:
        report = CostReport(
            framework="hipaa",
            total_requirements=5,
            automated_count=2,
            semi_automated_count=2,
            manual_count=1,
            total_hours_manual=100.0,
            total_hours_automated=30.0,
            total_cost_manual=15000.0,
            total_cost_with_automation=4500.0,
            savings_percentage=70.0,
            hourly_rate=150.0,
            requirement_details=(),
        )
        summary = report.summary()
        assert "hipaa" in summary
        assert "%" in summary


# ---------------------------------------------------------------------------
# ComplianceCostCalculator tests
# ---------------------------------------------------------------------------


class TestComplianceCostCalculatorConstruction:
    def test_default_hourly_rate(self) -> None:
        calc = ComplianceCostCalculator()
        assert calc.hourly_rate == 150.0

    def test_custom_hourly_rate(self) -> None:
        calc = ComplianceCostCalculator(hourly_rate=200.0)
        assert calc.hourly_rate == 200.0

    def test_invalid_hourly_rate_raises(self) -> None:
        with pytest.raises(ValueError):
            ComplianceCostCalculator(hourly_rate=0.0)

    def test_negative_hourly_rate_raises(self) -> None:
        with pytest.raises(ValueError):
            ComplianceCostCalculator(hourly_rate=-100.0)


class TestComplianceCostCalculatorCalculate:
    @pytest.fixture()
    def calc(self) -> ComplianceCostCalculator:
        return ComplianceCostCalculator(hourly_rate=150.0)

    def test_returns_cost_report(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert isinstance(report, CostReport)

    def test_framework_name_preserved(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert report.framework == "eu_ai_act"

    def test_total_requirements_matches_catalogue(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert report.total_requirements == len(EU_AI_ACT_REQUIREMENTS)

    def test_gdpr_requirements_count(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("gdpr", {})
        assert report.total_requirements == len(GDPR_REQUIREMENTS)

    def test_hipaa_requirements_count(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("hipaa", {})
        assert report.total_requirements == len(HIPAA_REQUIREMENTS)

    def test_automated_cost_less_than_manual(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert report.total_cost_with_automation < report.total_cost_manual

    def test_savings_percentage_positive(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert report.savings_percentage > 0.0

    def test_savings_percentage_max_100(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert report.savings_percentage <= 100.0

    def test_hourly_rate_preserved_in_report(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert report.hourly_rate == 150.0

    def test_automation_coverage_override_reduces_cost(self, calc: ComplianceCostCalculator) -> None:
        # Override a manual requirement to fully_automated
        manual_reqs = [r for r in EU_AI_ACT_REQUIREMENTS if r.automation_level == "manual"]
        if not manual_reqs:
            pytest.skip("No manual requirements in catalogue")
        req = manual_reqs[0]
        baseline = calc.calculate("eu_ai_act", {})
        overridden = calc.calculate("eu_ai_act", {req.requirement_id: "fully_automated"})
        assert overridden.total_cost_with_automation < baseline.total_cost_with_automation

    def test_all_automated_coverage_minimises_cost(self, calc: ComplianceCostCalculator) -> None:
        full_automation = {r.requirement_id: "fully_automated" for r in EU_AI_ACT_REQUIREMENTS}
        report = calc.calculate("eu_ai_act", full_automation)
        assert report.automated_count == len(EU_AI_ACT_REQUIREMENTS)

    def test_requirement_details_length_matches_requirements(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        assert len(report.requirement_details) == report.total_requirements

    def test_requirement_details_have_cost_fields(self, calc: ComplianceCostCalculator) -> None:
        report = calc.calculate("eu_ai_act", {})
        for detail in report.requirement_details:
            assert "cost_manual" in detail
            assert "cost_automated" in detail
            assert "savings" in detail

    def test_unknown_framework_raises_key_error(self, calc: ComplianceCostCalculator) -> None:
        with pytest.raises(KeyError):
            calc.calculate("unknown_framework", {})

    def test_automated_count_plus_semi_plus_manual_equals_total(
        self, calc: ComplianceCostCalculator
    ) -> None:
        report = calc.calculate("eu_ai_act", {})
        total = report.automated_count + report.semi_automated_count + report.manual_count
        assert total == report.total_requirements


class TestComplianceCostCalculatorCompareScenarios:
    @pytest.fixture()
    def calc(self) -> ComplianceCostCalculator:
        return ComplianceCostCalculator(hourly_rate=150.0)

    def test_returns_comparison_report(self, calc: ComplianceCostCalculator) -> None:
        result = calc.compare_scenarios("eu_ai_act", [
            {"label": "baseline", "automation_coverage": {}},
        ])
        assert isinstance(result, ComparisonReport)

    def test_comparison_has_correct_number_of_scenarios(self, calc: ComplianceCostCalculator) -> None:
        scenarios = [
            {"label": "baseline", "automation_coverage": {}},
            {"label": "full_automation", "automation_coverage": {r.requirement_id: "fully_automated" for r in EU_AI_ACT_REQUIREMENTS}},
        ]
        result = calc.compare_scenarios("eu_ai_act", scenarios)
        assert len(result.scenarios) == 2

    def test_best_scenario_is_lowest_cost(self, calc: ComplianceCostCalculator) -> None:
        full_automation = {r.requirement_id: "fully_automated" for r in EU_AI_ACT_REQUIREMENTS}
        scenarios = [
            {"label": "baseline", "automation_coverage": {}},
            {"label": "full_auto", "automation_coverage": full_automation},
        ]
        result = calc.compare_scenarios("eu_ai_act", scenarios)
        best = result.best_scenario()
        assert best is not None
        assert best[0] == "full_auto"

    def test_framework_name_in_comparison(self, calc: ComplianceCostCalculator) -> None:
        result = calc.compare_scenarios("gdpr", [
            {"label": "s", "automation_coverage": {}},
        ])
        assert result.framework == "gdpr"

    def test_comparison_to_dict_is_serializable(self, calc: ComplianceCostCalculator) -> None:
        import json
        result = calc.compare_scenarios("hipaa", [
            {"label": "s1", "automation_coverage": {}},
            {"label": "s2", "automation_coverage": {}},
        ])
        json_str = json.dumps(result.to_dict())
        assert len(json_str) > 0


# ---------------------------------------------------------------------------
# Framework maps tests
# ---------------------------------------------------------------------------


class TestFrameworkMaps:
    def test_list_frameworks(self) -> None:
        frameworks = list_frameworks()
        assert "eu_ai_act" in frameworks
        assert "gdpr" in frameworks
        assert "hipaa" in frameworks

    def test_get_requirements_eu_ai_act(self) -> None:
        reqs = get_requirements("eu_ai_act")
        assert len(reqs) > 0
        assert all(r.framework == "eu_ai_act" for r in reqs)

    def test_get_requirements_gdpr(self) -> None:
        reqs = get_requirements("gdpr")
        assert len(reqs) > 0
        assert all(r.framework == "gdpr" for r in reqs)

    def test_get_requirements_hipaa(self) -> None:
        reqs = get_requirements("hipaa")
        assert len(reqs) > 0
        assert all(r.framework == "hipaa" for r in reqs)

    def test_get_requirements_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            get_requirements("unknown")

    def test_all_requirements_have_positive_manual_hours(self) -> None:
        for framework in list_frameworks():
            for req in get_requirements(framework):
                assert req.estimated_hours_manual > 0, f"{req.requirement_id} has non-positive manual hours"

    def test_all_requirements_automated_hours_less_than_manual(self) -> None:
        for framework in list_frameworks():
            for req in get_requirements(framework):
                assert req.estimated_hours_automated <= req.estimated_hours_manual, (
                    f"{req.requirement_id}: automated ({req.estimated_hours_automated}) "
                    f"> manual ({req.estimated_hours_manual})"
                )

    def test_all_requirements_valid_automation_levels(self) -> None:
        valid_levels = {"fully_automated", "semi_automated", "manual"}
        for framework in list_frameworks():
            for req in get_requirements(framework):
                assert req.automation_level in valid_levels, (
                    f"{req.requirement_id} has invalid automation level: {req.automation_level!r}"
                )

    def test_requirement_ids_unique_within_framework(self) -> None:
        for framework in list_frameworks():
            reqs = get_requirements(framework)
            ids = [r.requirement_id for r in reqs]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {framework}"

    def test_eu_ai_act_has_a6_requirement(self) -> None:
        reqs = get_requirements("eu_ai_act")
        ids = {r.requirement_id for r in reqs}
        assert any("A6" in req_id for req_id in ids)

    def test_gdpr_has_dpia_requirement(self) -> None:
        reqs = get_requirements("gdpr")
        ids = {r.requirement_id for r in reqs}
        assert any("dpia" in req_id.lower() or "A35" in req_id for req_id in ids)

    def test_hipaa_has_encryption_requirement(self) -> None:
        reqs = get_requirements("hipaa")
        ids = {r.requirement_id for r in reqs}
        assert any("encrypt" in req_id.lower() for req_id in ids)


# ---------------------------------------------------------------------------
# CostReportRenderer tests
# ---------------------------------------------------------------------------


class TestCostReportRenderer:
    @pytest.fixture()
    def renderer(self) -> CostReportRenderer:
        return CostReportRenderer()

    @pytest.fixture()
    def report(self) -> CostReport:
        calc = ComplianceCostCalculator(hourly_rate=150.0)
        return calc.calculate("eu_ai_act", {})

    def test_to_markdown_returns_string(self, renderer: CostReportRenderer, report: CostReport) -> None:
        md = renderer.to_markdown(report)
        assert isinstance(md, str)
        assert len(md) > 0

    def test_to_markdown_contains_framework_name(self, renderer: CostReportRenderer, report: CostReport) -> None:
        md = renderer.to_markdown(report)
        assert "Eu Ai Act" in md or "eu_ai_act" in md.lower() or "EU AI ACT" in md

    def test_to_markdown_contains_savings(self, renderer: CostReportRenderer, report: CostReport) -> None:
        md = renderer.to_markdown(report)
        assert "Savings" in md

    def test_to_markdown_contains_dollar_sign(self, renderer: CostReportRenderer, report: CostReport) -> None:
        md = renderer.to_markdown(report)
        assert "$" in md

    def test_to_text_summary_returns_string(self, renderer: CostReportRenderer, report: CostReport) -> None:
        summary = renderer.to_text_summary(report)
        assert isinstance(summary, str)
        assert "%" in summary

    def test_comparison_to_markdown_returns_string(self, renderer: CostReportRenderer) -> None:
        calc = ComplianceCostCalculator(hourly_rate=150.0)
        comparison = calc.compare_scenarios("gdpr", [
            {"label": "baseline", "automation_coverage": {}},
            {"label": "optimised", "automation_coverage": {r.requirement_id: "fully_automated" for r in GDPR_REQUIREMENTS}},
        ])
        md = renderer.comparison_to_markdown(comparison)
        assert "Comparison" in md
        assert "baseline" in md
        assert "optimised" in md

    def test_custom_currency_symbol(self) -> None:
        renderer = CostReportRenderer(currency_symbol="£")
        calc = ComplianceCostCalculator(hourly_rate=150.0)
        report = calc.calculate("gdpr", {})
        md = renderer.to_markdown(report)
        assert "£" in md

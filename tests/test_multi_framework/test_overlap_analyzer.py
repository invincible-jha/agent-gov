"""Tests for OverlapAnalyzer."""
from __future__ import annotations

import pytest

from agent_gov.multi_framework.mapper import SupportedFramework
from agent_gov.multi_framework.overlap_analyzer import (
    ControlGroup,
    OverlapAnalyzer,
    OverlapReport,
    SharedControl,
)


class TestSharedControl:
    def test_cross_framework_count(self) -> None:
        sc = SharedControl(
            tag="logging",
            frameworks=frozenset({SupportedFramework.GDPR, SupportedFramework.HIPAA, SupportedFramework.SOC2}),
            requirement_count=5,
        )
        assert sc.cross_framework_count == 3

    def test_is_hashable(self) -> None:
        sc = SharedControl(
            tag="access_control",
            frameworks=frozenset({SupportedFramework.HIPAA}),
            requirement_count=2,
        )
        assert sc in {sc}


class TestControlGroup:
    def test_add_requirement_updates_frameworks(self) -> None:
        from agent_gov.multi_framework.mapper import FrameworkRequirement
        group = ControlGroup(shared_tag="logging")
        req = FrameworkRequirement(
            framework=SupportedFramework.GDPR,
            requirement_id="Art30",
            name="Records",
            description="Maintain records.",
            category="auditability",
            control_tags=frozenset({"logging"}),
        )
        group.add_requirement(req)
        assert SupportedFramework.GDPR in group.frameworks_covered
        assert len(group.requirements) == 1

    def test_to_dict_structure(self) -> None:
        from agent_gov.multi_framework.mapper import FrameworkRequirement
        group = ControlGroup(shared_tag="logging")
        req = FrameworkRequirement(
            framework=SupportedFramework.HIPAA,
            requirement_id="164.312b",
            name="Audit controls",
            description="Audit controls.",
            category="auditability",
            control_tags=frozenset({"logging", "auditability"}),
        )
        group.add_requirement(req)
        d = group.to_dict()
        assert d["shared_tag"] == "logging"
        assert len(d["requirements"]) == 1
        assert "HIPAA" in d["frameworks_covered"]


class TestOverlapAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = OverlapAnalyzer(min_frameworks=2)

    def test_analyze_returns_overlap_report(self) -> None:
        report = self.analyzer.analyze()
        assert isinstance(report, OverlapReport)

    def test_total_requirements_analyzed_is_positive(self) -> None:
        report = self.analyzer.analyze()
        assert report.total_requirements_analyzed > 0

    def test_control_groups_not_empty(self) -> None:
        report = self.analyzer.analyze()
        assert len(report.control_groups) > 0

    def test_shared_controls_not_empty(self) -> None:
        report = self.analyzer.analyze()
        assert len(report.shared_controls) > 0

    def test_most_shared_control_is_not_none(self) -> None:
        report = self.analyzer.analyze()
        most_shared = report.most_shared_control
        assert most_shared is not None
        assert most_shared.cross_framework_count >= 2

    def test_all_shared_controls_meet_min_frameworks(self) -> None:
        report = self.analyzer.analyze()
        for sc in report.shared_controls:
            assert sc.cross_framework_count >= 2

    def test_groups_sorted_by_frameworks_covered_descending(self) -> None:
        report = self.analyzer.analyze()
        counts = [len(g.frameworks_covered) for g in report.control_groups]
        assert counts == sorted(counts, reverse=True)

    def test_report_to_dict_structure(self) -> None:
        report = self.analyzer.analyze()
        d = report.to_dict()
        assert "total_requirements_analyzed" in d
        assert "control_group_count" in d
        assert "shared_controls" in d
        assert "control_groups" in d

    def test_groups_for_framework(self) -> None:
        report = self.analyzer.analyze()
        gdpr_groups = report.groups_for_framework(SupportedFramework.GDPR)
        for group in gdpr_groups:
            assert SupportedFramework.GDPR in group.frameworks_covered

    def test_min_frameworks_three_reduces_groups(self) -> None:
        analyzer_two = OverlapAnalyzer(min_frameworks=2)
        analyzer_three = OverlapAnalyzer(min_frameworks=3)
        report_two = analyzer_two.analyze()
        report_three = analyzer_three.analyze()
        # More restrictive threshold should produce fewer or equal groups
        assert len(report_three.control_groups) <= len(report_two.control_groups)

    def test_find_redundant_requirements(self) -> None:
        redundant = self.analyzer.find_redundant_requirements(
            SupportedFramework.EU_AI_ACT,
            similarity_threshold=0.3,
        )
        assert isinstance(redundant, list)
        if redundant:
            source_req, similar = redundant[0]
            assert source_req.framework == SupportedFramework.EU_AI_ACT
            assert len(similar) > 0

    def test_find_redundant_requirements_high_threshold_is_subset(self) -> None:
        low = self.analyzer.find_redundant_requirements(
            SupportedFramework.GDPR, similarity_threshold=0.2
        )
        high = self.analyzer.find_redundant_requirements(
            SupportedFramework.GDPR, similarity_threshold=0.8
        )
        assert len(high) <= len(low)

"""Tests for CrossFrameworkMapper."""
from __future__ import annotations

import pytest

from agent_gov.multi_framework.mapper import (
    CrossFrameworkMapper,
    FrameworkRequirement,
    MappingResult,
    RequirementMatch,
    SupportedFramework,
    _jaccard_similarity,
)


class TestJaccardSimilarity:
    def test_identical_sets_return_one(self) -> None:
        tags = frozenset({"a", "b", "c"})
        assert _jaccard_similarity(tags, tags) == 1.0

    def test_disjoint_sets_return_zero(self) -> None:
        assert _jaccard_similarity(frozenset({"a"}), frozenset({"b"})) == 0.0

    def test_partial_overlap(self) -> None:
        a = frozenset({"a", "b", "c"})
        b = frozenset({"b", "c", "d"})
        score = _jaccard_similarity(a, b)
        # intersection=2, union=4 → 0.5
        assert score == pytest.approx(0.5)

    def test_empty_sets_return_zero(self) -> None:
        assert _jaccard_similarity(frozenset(), frozenset()) == 0.0

    def test_one_empty_set(self) -> None:
        assert _jaccard_similarity(frozenset({"a"}), frozenset()) == 0.0


class TestFrameworkRequirement:
    def test_frozen_dataclass_is_hashable(self) -> None:
        req = FrameworkRequirement(
            framework=SupportedFramework.GDPR,
            requirement_id="Art30",
            name="Records",
            description="Maintain records.",
            category="auditability",
            control_tags=frozenset({"logging", "auditability"}),
        )
        # Should be hashable and usable in sets
        assert req in {req}

    def test_can_be_stored_in_dict(self) -> None:
        req = FrameworkRequirement(
            framework=SupportedFramework.HIPAA,
            requirement_id="164.312b",
            name="Audit controls",
            description="Audit controls.",
            category="auditability",
            control_tags=frozenset({"logging"}),
        )
        mapping: dict[FrameworkRequirement, str] = {req: "value"}
        assert mapping[req] == "value"


class TestCrossFrameworkMapper:
    def setup_method(self) -> None:
        self.mapper = CrossFrameworkMapper()

    def test_get_known_requirement(self) -> None:
        req = self.mapper.get_requirement("EU_AI_ACT", "Art13")
        assert req is not None
        assert req.framework == SupportedFramework.EU_AI_ACT
        assert req.requirement_id == "Art13"
        assert req.name == "Transparency to users"

    def test_get_unknown_requirement_returns_none(self) -> None:
        req = self.mapper.get_requirement("EU_AI_ACT", "NONEXISTENT")
        assert req is None

    def test_get_requirement_accepts_enum(self) -> None:
        req = self.mapper.get_requirement(SupportedFramework.GDPR, "Art30")
        assert req is not None
        assert req.framework == SupportedFramework.GDPR

    def test_map_requirement_returns_mapping_result(self) -> None:
        result = self.mapper.map_requirement("EU_AI_ACT", "Art13")
        assert isinstance(result, MappingResult)
        assert result.source_framework == SupportedFramework.EU_AI_ACT
        assert result.source_requirement_id == "Art13"

    def test_map_requirement_excludes_same_framework_by_default(self) -> None:
        result = self.mapper.map_requirement("EU_AI_ACT", "Art13")
        for match in result.matches:
            assert match.framework != SupportedFramework.EU_AI_ACT

    def test_map_requirement_matches_are_sorted_descending(self) -> None:
        result = self.mapper.map_requirement("EU_AI_ACT", "Art13")
        scores = [m.similarity_score for m in result.matches]
        assert scores == sorted(scores, reverse=True)

    def test_map_requirement_transparency_has_gdpr_match(self) -> None:
        result = self.mapper.map_requirement("EU_AI_ACT", "Art13")
        matched_frameworks = {m.framework for m in result.matches}
        assert SupportedFramework.GDPR in matched_frameworks

    def test_map_requirement_raises_on_unknown(self) -> None:
        with pytest.raises(KeyError):
            self.mapper.map_requirement("EU_AI_ACT", "NONEXISTENT")

    def test_map_requirement_top_match(self) -> None:
        result = self.mapper.map_requirement("EU_AI_ACT", "Art13")
        top = result.top_match
        assert top is not None
        assert isinstance(top, RequirementMatch)

    def test_map_requirement_shared_tags_are_subset(self) -> None:
        source = self.mapper.get_requirement("EU_AI_ACT", "Art12")
        assert source is not None
        result = self.mapper.map_requirement("EU_AI_ACT", "Art12")
        for match in result.matches:
            assert match.shared_tags.issubset(source.control_tags)

    def test_map_all_requirements(self) -> None:
        results = self.mapper.map_all_requirements("EU_AI_ACT")
        assert len(results) > 0
        for result in results:
            assert result.source_framework == SupportedFramework.EU_AI_ACT

    def test_list_requirements_returns_all(self) -> None:
        requirements = self.mapper.list_requirements("EU_AI_ACT")
        assert len(requirements) >= 5

    def test_find_by_category_transparency(self) -> None:
        reqs = self.mapper.find_by_category("transparency")
        assert len(reqs) >= 2
        for req in reqs:
            assert req.category == "transparency"

    def test_find_by_category_with_framework_filter(self) -> None:
        reqs = self.mapper.find_by_category(
            "risk_management",
            frameworks=[SupportedFramework.GDPR, SupportedFramework.HIPAA],
        )
        for req in reqs:
            assert req.framework in {SupportedFramework.GDPR, SupportedFramework.HIPAA}

    def test_find_by_tag(self) -> None:
        reqs = self.mapper.find_by_tag("logging")
        assert len(reqs) >= 2
        for req in reqs:
            assert "logging" in req.control_tags

    def test_mapping_result_to_dict(self) -> None:
        result = self.mapper.map_requirement("GDPR", "Art30")
        d = result.to_dict()
        assert d["source_framework"] == "GDPR"
        assert d["source_requirement_id"] == "Art30"
        assert isinstance(d["matches"], list)

    def test_similarity_threshold_filters_low_scores(self) -> None:
        high_threshold_mapper = CrossFrameworkMapper(similarity_threshold=0.9)
        result = high_threshold_mapper.map_requirement("EU_AI_ACT", "Art13")
        for match in result.matches:
            assert match.similarity_score >= 0.9

    def test_all_supported_frameworks_have_requirements(self) -> None:
        for fw in SupportedFramework:
            requirements = self.mapper.list_requirements(fw)
            assert len(requirements) > 0, f"{fw.value} has no requirements"

    def test_map_hipaa_auditability_to_gdpr(self) -> None:
        result = self.mapper.map_requirement("HIPAA", "164.312b")
        gdpr_matches = [m for m in result.matches if m.framework == SupportedFramework.GDPR]
        assert len(gdpr_matches) > 0

    def test_soc2_risk_maps_to_other_frameworks(self) -> None:
        result = self.mapper.map_requirement("SOC2", "CC4.1")
        assert len(result.matches) > 0

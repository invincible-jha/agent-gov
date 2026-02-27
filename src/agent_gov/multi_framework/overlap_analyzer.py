"""OverlapAnalyzer — identify shared controls across compliance frameworks.

Finds groups of requirements from different frameworks that share the same
underlying controls, enabling a single implementation to satisfy multiple
regulatory obligations.

Example
-------
::

    from agent_gov.multi_framework.overlap_analyzer import OverlapAnalyzer

    analyzer = OverlapAnalyzer()
    report = analyzer.analyze()
    for group in report.control_groups:
        print(group.shared_tag, [r.requirement_id for r in group.requirements])
"""
from __future__ import annotations

from dataclasses import dataclass, field

from agent_gov.multi_framework.mapper import (
    CrossFrameworkMapper,
    FrameworkRequirement,
    SupportedFramework,
    _jaccard_similarity,
)


@dataclass(frozen=True)
class SharedControl:
    """A control tag shared by requirements across multiple frameworks.

    Attributes
    ----------
    tag:
        The normalized control keyword shared across requirements.
    frameworks:
        Set of frameworks that have at least one requirement with this tag.
    requirement_count:
        Total number of requirements that include this tag.
    """

    tag: str
    frameworks: frozenset[SupportedFramework]
    requirement_count: int

    @property
    def cross_framework_count(self) -> int:
        """Number of distinct frameworks sharing this control."""
        return len(self.frameworks)


@dataclass
class ControlGroup:
    """A group of requirements from different frameworks sharing a control tag.

    Attributes
    ----------
    shared_tag:
        The control keyword that groups these requirements.
    requirements:
        Requirements from different frameworks sharing this control tag.
    frameworks_covered:
        Set of frameworks represented in this group.
    """

    shared_tag: str
    requirements: list[FrameworkRequirement] = field(default_factory=list)
    frameworks_covered: set[SupportedFramework] = field(default_factory=set)

    def add_requirement(self, req: FrameworkRequirement) -> None:
        """Add a requirement to this group."""
        self.requirements.append(req)
        self.frameworks_covered.add(req.framework)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "shared_tag": self.shared_tag,
            "frameworks_covered": sorted(fw.value for fw in self.frameworks_covered),
            "requirement_count": len(self.requirements),
            "requirements": [
                {
                    "framework": r.framework.value,
                    "requirement_id": r.requirement_id,
                    "name": r.name,
                    "category": r.category,
                }
                for r in self.requirements
            ],
        }


@dataclass
class OverlapReport:
    """Full overlap analysis report across all frameworks.

    Attributes
    ----------
    control_groups:
        Groups of requirements sharing the same control tag.
        Sorted by number of frameworks covered (descending).
    shared_controls:
        Summary of each control tag and how many frameworks share it.
    total_requirements_analyzed:
        Total number of requirements examined across all frameworks.
    """

    control_groups: list[ControlGroup] = field(default_factory=list)
    shared_controls: list[SharedControl] = field(default_factory=list)
    total_requirements_analyzed: int = 0

    @property
    def most_shared_control(self) -> SharedControl | None:
        """Return the control shared by the most frameworks."""
        if not self.shared_controls:
            return None
        return max(self.shared_controls, key=lambda c: c.cross_framework_count)

    def groups_for_framework(self, framework: SupportedFramework) -> list[ControlGroup]:
        """Return groups that include requirements from the given framework."""
        return [
            g for g in self.control_groups
            if framework in g.frameworks_covered
        ]

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "total_requirements_analyzed": self.total_requirements_analyzed,
            "control_group_count": len(self.control_groups),
            "shared_controls": [
                {
                    "tag": sc.tag,
                    "cross_framework_count": sc.cross_framework_count,
                    "requirement_count": sc.requirement_count,
                    "frameworks": sorted(fw.value for fw in sc.frameworks),
                }
                for sc in self.shared_controls
            ],
            "control_groups": [g.to_dict() for g in self.control_groups],
        }


class OverlapAnalyzer:
    """Identify shared controls across EU AI Act, GDPR, HIPAA, and SOC2.

    Uses the requirement catalog from CrossFrameworkMapper to find which
    control tags appear in requirements from multiple frameworks, grouping
    requirements by shared control.

    Parameters
    ----------
    min_frameworks:
        Minimum number of distinct frameworks a control tag must appear in
        to be included in the overlap report. Defaults to 2.

    Example
    -------
    ::

        analyzer = OverlapAnalyzer(min_frameworks=2)
        report = analyzer.analyze()
        print(report.most_shared_control.tag)
    """

    def __init__(self, *, min_frameworks: int = 2) -> None:
        self._min_frameworks = min_frameworks
        self._mapper = CrossFrameworkMapper()

    def analyze(self) -> OverlapReport:
        """Run a full overlap analysis across all supported frameworks.

        Returns
        -------
        OverlapReport
            Groups of overlapping requirements with shared control tags.
        """
        all_requirements: list[FrameworkRequirement] = []
        for fw in SupportedFramework:
            all_requirements.extend(self._mapper.list_requirements(fw))

        # Collect all tags and which frameworks + requirements use them
        tag_to_requirements: dict[str, list[FrameworkRequirement]] = {}
        tag_to_frameworks: dict[str, set[SupportedFramework]] = {}

        for req in all_requirements:
            for tag in req.control_tags:
                tag_to_requirements.setdefault(tag, []).append(req)
                tag_to_frameworks.setdefault(tag, set()).add(req.framework)

        # Build shared controls and groups filtered by min_frameworks
        shared_controls: list[SharedControl] = []
        control_groups: list[ControlGroup] = []

        for tag, frameworks in tag_to_frameworks.items():
            if len(frameworks) < self._min_frameworks:
                continue

            requirements = tag_to_requirements[tag]
            shared_controls.append(
                SharedControl(
                    tag=tag,
                    frameworks=frozenset(frameworks),
                    requirement_count=len(requirements),
                )
            )

            group = ControlGroup(shared_tag=tag)
            for req in requirements:
                if req.framework in frameworks:
                    group.add_requirement(req)
            control_groups.append(group)

        # Sort by number of frameworks covered descending
        shared_controls.sort(key=lambda sc: sc.cross_framework_count, reverse=True)
        control_groups.sort(key=lambda g: len(g.frameworks_covered), reverse=True)

        return OverlapReport(
            control_groups=control_groups,
            shared_controls=shared_controls,
            total_requirements_analyzed=len(all_requirements),
        )

    def find_redundant_requirements(
        self,
        framework: SupportedFramework,
        *,
        similarity_threshold: float = 0.5,
    ) -> list[tuple[FrameworkRequirement, list[FrameworkRequirement]]]:
        """Find requirements in a framework that are highly redundant with others.

        Returns a list of (requirement, similar_requirements_from_other_frameworks).
        A requirement is considered redundant if it has at least one match in
        another framework above the similarity threshold.

        Parameters
        ----------
        framework:
            The framework to analyze for redundant requirements.
        similarity_threshold:
            Minimum Jaccard similarity for two requirements to be considered
            redundant. Defaults to 0.5.
        """
        source_requirements = self._mapper.list_requirements(framework)
        result: list[tuple[FrameworkRequirement, list[FrameworkRequirement]]] = []

        for source_req in source_requirements:
            similar: list[FrameworkRequirement] = []
            for fw in SupportedFramework:
                if fw == framework:
                    continue
                for target_req in self._mapper.list_requirements(fw):
                    score = _jaccard_similarity(source_req.control_tags, target_req.control_tags)
                    if score >= similarity_threshold:
                        similar.append(target_req)
            if similar:
                result.append((source_req, similar))

        return result

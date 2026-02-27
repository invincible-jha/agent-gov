"""CrossFrameworkMapper — map compliance requirements across EU AI Act, GDPR, HIPAA, SOC2.

Identifies overlapping requirements so organizations can implement shared controls
and reduce duplicated compliance effort.

Example
-------
::

    from agent_gov.multi_framework.mapper import CrossFrameworkMapper

    mapper = CrossFrameworkMapper()
    result = mapper.map_requirement("EU_AI_ACT", "transparency_obligation")
    for match in result.matches:
        print(match.framework, match.requirement_id, match.similarity_score)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SupportedFramework(str, Enum):
    """Supported compliance frameworks for cross-mapping."""

    EU_AI_ACT = "EU_AI_ACT"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOC2 = "SOC2"


@dataclass(frozen=True)
class FrameworkRequirement:
    """A single compliance requirement within a framework.

    Attributes
    ----------
    framework:
        The framework this requirement belongs to.
    requirement_id:
        Unique identifier within the framework (e.g. ``"Art13"``).
    name:
        Short human-readable name for the requirement.
    description:
        Full description of what must be done to satisfy the requirement.
    category:
        Logical category such as ``"transparency"``, ``"data_protection"``,
        ``"access_control"``, ``"auditability"``.
    control_tags:
        Set of normalized control keywords used for overlap detection.
    """

    framework: SupportedFramework
    requirement_id: str
    name: str
    description: str
    category: str
    control_tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class RequirementMatch:
    """A match between a source requirement and a requirement in another framework.

    Attributes
    ----------
    framework:
        The target framework containing the matched requirement.
    requirement_id:
        The matched requirement's ID within the target framework.
    requirement_name:
        Human-readable name of the matched requirement.
    similarity_score:
        Float from 0.0 to 1.0 measuring how well the control tags overlap.
    shared_tags:
        The control tags shared between the source and target requirements.
    """

    framework: SupportedFramework
    requirement_id: str
    requirement_name: str
    similarity_score: float
    shared_tags: frozenset[str]


@dataclass
class MappingResult:
    """Result of mapping a requirement to equivalent requirements in other frameworks.

    Attributes
    ----------
    source_framework:
        The framework the source requirement comes from.
    source_requirement_id:
        The ID of the source requirement.
    source_requirement_name:
        Human-readable name of the source requirement.
    matches:
        List of matching requirements sorted by descending similarity score.
    """

    source_framework: SupportedFramework
    source_requirement_id: str
    source_requirement_name: str
    matches: list[RequirementMatch] = field(default_factory=list)

    @property
    def top_match(self) -> Optional[RequirementMatch]:
        """Return the highest-scoring match, or None if there are no matches."""
        return self.matches[0] if self.matches else None

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "source_framework": self.source_framework.value,
            "source_requirement_id": self.source_requirement_id,
            "source_requirement_name": self.source_requirement_name,
            "matches": [
                {
                    "framework": m.framework.value,
                    "requirement_id": m.requirement_id,
                    "requirement_name": m.requirement_name,
                    "similarity_score": m.similarity_score,
                    "shared_tags": sorted(m.shared_tags),
                }
                for m in self.matches
            ],
        }


def _build_requirement_catalog() -> dict[SupportedFramework, list[FrameworkRequirement]]:
    """Build the built-in cross-framework requirement catalog."""
    eu = SupportedFramework.EU_AI_ACT
    gdpr = SupportedFramework.GDPR
    hipaa = SupportedFramework.HIPAA
    soc2 = SupportedFramework.SOC2

    catalog: dict[SupportedFramework, list[FrameworkRequirement]] = {
        eu: [
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art13",
                name="Transparency to users",
                description="High-risk AI systems must provide clear information to users.",
                category="transparency",
                control_tags=frozenset({"transparency", "user_notice", "disclosure", "documentation"}),
            ),
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art14",
                name="Human oversight",
                description="High-risk AI systems must enable human oversight and intervention.",
                category="human_oversight",
                control_tags=frozenset({"human_oversight", "auditability", "control", "intervention"}),
            ),
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art15",
                name="Accuracy and robustness",
                description="High-risk AI systems must achieve appropriate accuracy and be robust.",
                category="reliability",
                control_tags=frozenset({"accuracy", "robustness", "reliability", "testing"}),
            ),
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art17",
                name="Quality management system",
                description="Providers must have a quality management system for high-risk AI.",
                category="governance",
                control_tags=frozenset({"governance", "quality", "documentation", "risk_management"}),
            ),
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art9",
                name="Risk management system",
                description="Providers must establish and maintain a risk management system.",
                category="risk_management",
                control_tags=frozenset({"risk_management", "risk_assessment", "documentation", "governance"}),
            ),
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art10",
                name="Data and data governance",
                description="Training data must meet quality criteria and be subject to governance.",
                category="data_governance",
                control_tags=frozenset({"data_governance", "data_quality", "data_protection", "access_control"}),
            ),
            FrameworkRequirement(
                framework=eu,
                requirement_id="Art12",
                name="Record-keeping",
                description="High-risk AI systems must automatically log events during operation.",
                category="auditability",
                control_tags=frozenset({"logging", "auditability", "record_keeping", "monitoring"}),
            ),
        ],
        gdpr: [
            FrameworkRequirement(
                framework=gdpr,
                requirement_id="Art13-14",
                name="Information to data subjects",
                description="Controllers must provide transparent information about data processing.",
                category="transparency",
                control_tags=frozenset({"transparency", "user_notice", "disclosure", "data_protection"}),
            ),
            FrameworkRequirement(
                framework=gdpr,
                requirement_id="Art22",
                name="Automated decision-making",
                description="Data subjects have rights regarding automated decisions including profiling.",
                category="human_oversight",
                control_tags=frozenset({"human_oversight", "automated_decision", "transparency", "control"}),
            ),
            FrameworkRequirement(
                framework=gdpr,
                requirement_id="Art25",
                name="Data protection by design",
                description="Controllers must implement data protection by design and by default.",
                category="data_protection",
                control_tags=frozenset({"data_protection", "privacy_by_design", "access_control", "data_minimization"}),
            ),
            FrameworkRequirement(
                framework=gdpr,
                requirement_id="Art30",
                name="Records of processing activities",
                description="Controllers must maintain records of all processing activities.",
                category="auditability",
                control_tags=frozenset({"logging", "auditability", "record_keeping", "documentation"}),
            ),
            FrameworkRequirement(
                framework=gdpr,
                requirement_id="Art35",
                name="Data protection impact assessment",
                description="High-risk processing requires a DPIA before processing begins.",
                category="risk_management",
                control_tags=frozenset({"risk_assessment", "risk_management", "data_protection", "documentation"}),
            ),
            FrameworkRequirement(
                framework=gdpr,
                requirement_id="Art32",
                name="Security of processing",
                description="Appropriate technical and organisational security measures must be implemented.",
                category="security",
                control_tags=frozenset({"security", "encryption", "access_control", "integrity"}),
            ),
        ],
        hipaa: [
            FrameworkRequirement(
                framework=hipaa,
                requirement_id="164.312a",
                name="Access control",
                description="Implement technical policies and procedures for access to ePHI.",
                category="access_control",
                control_tags=frozenset({"access_control", "authentication", "authorization", "security"}),
            ),
            FrameworkRequirement(
                framework=hipaa,
                requirement_id="164.312b",
                name="Audit controls",
                description="Implement hardware, software, and procedural mechanisms for audit.",
                category="auditability",
                control_tags=frozenset({"logging", "auditability", "record_keeping", "monitoring"}),
            ),
            FrameworkRequirement(
                framework=hipaa,
                requirement_id="164.312c",
                name="Integrity controls",
                description="Implement policies to protect ePHI from improper alteration or destruction.",
                category="integrity",
                control_tags=frozenset({"integrity", "data_protection", "security", "validation"}),
            ),
            FrameworkRequirement(
                framework=hipaa,
                requirement_id="164.308a1",
                name="Risk analysis",
                description="Conduct an accurate and thorough assessment of potential risks to ePHI.",
                category="risk_management",
                control_tags=frozenset({"risk_assessment", "risk_management", "documentation", "security"}),
            ),
            FrameworkRequirement(
                framework=hipaa,
                requirement_id="164.530i",
                name="Privacy policies",
                description="Covered entities must have written privacy policies and procedures.",
                category="data_protection",
                control_tags=frozenset({"data_protection", "documentation", "governance", "privacy_by_design"}),
            ),
            FrameworkRequirement(
                framework=hipaa,
                requirement_id="164.524",
                name="Individual access",
                description="Individuals have the right to access their own PHI.",
                category="transparency",
                control_tags=frozenset({"transparency", "user_notice", "disclosure", "access_control"}),
            ),
        ],
        soc2: [
            FrameworkRequirement(
                framework=soc2,
                requirement_id="CC6.1",
                name="Logical and physical access controls",
                description="Implement logical access controls to prevent unauthorized access.",
                category="access_control",
                control_tags=frozenset({"access_control", "authentication", "authorization", "security"}),
            ),
            FrameworkRequirement(
                framework=soc2,
                requirement_id="CC7.2",
                name="System monitoring",
                description="Monitor system components for anomalies that indicate malicious acts.",
                category="monitoring",
                control_tags=frozenset({"monitoring", "logging", "auditability", "security"}),
            ),
            FrameworkRequirement(
                framework=soc2,
                requirement_id="CC4.1",
                name="Risk assessment",
                description="Identify and assess risks from internal and external sources.",
                category="risk_management",
                control_tags=frozenset({"risk_assessment", "risk_management", "governance", "documentation"}),
            ),
            FrameworkRequirement(
                framework=soc2,
                requirement_id="CC1.1",
                name="Control environment",
                description="Demonstrate commitment to integrity and ethical values in controls.",
                category="governance",
                control_tags=frozenset({"governance", "quality", "documentation", "accountability"}),
            ),
            FrameworkRequirement(
                framework=soc2,
                requirement_id="P1.1",
                name="Privacy notice",
                description="Provide notice about personal information collection and use practices.",
                category="transparency",
                control_tags=frozenset({"transparency", "user_notice", "disclosure", "data_protection"}),
            ),
            FrameworkRequirement(
                framework=soc2,
                requirement_id="CC9.1",
                name="Risk mitigation",
                description="Identify and select risk mitigation strategies for identified risks.",
                category="risk_management",
                control_tags=frozenset({"risk_management", "risk_assessment", "control", "documentation"}),
            ),
            FrameworkRequirement(
                framework=soc2,
                requirement_id="A1.1",
                name="Availability monitoring",
                description="Current processing capacity is used to manage availability of outputs.",
                category="reliability",
                control_tags=frozenset({"reliability", "monitoring", "availability", "testing"}),
            ),
        ],
    }
    return catalog


def _jaccard_similarity(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    """Compute Jaccard similarity between two tag sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return intersection / union


class CrossFrameworkMapper:
    """Map compliance requirements across EU AI Act, GDPR, HIPAA, and SOC2.

    Uses tag-based Jaccard similarity to find equivalent requirements across
    frameworks, allowing organizations to identify shared controls and reduce
    duplicated compliance effort.

    Parameters
    ----------
    similarity_threshold:
        Minimum Jaccard similarity score (0.0–1.0) for a match to be included.
        Defaults to 0.2.

    Example
    -------
    ::

        mapper = CrossFrameworkMapper()
        result = mapper.map_requirement("EU_AI_ACT", "Art13")
        for match in result.matches:
            print(match.framework, match.similarity_score)
    """

    def __init__(self, *, similarity_threshold: float = 0.2) -> None:
        self._similarity_threshold = similarity_threshold
        self._catalog = _build_requirement_catalog()
        self._index: dict[tuple[SupportedFramework, str], FrameworkRequirement] = {}
        for requirements in self._catalog.values():
            for req in requirements:
                self._index[(req.framework, req.requirement_id)] = req

    def get_requirement(
        self,
        framework: str | SupportedFramework,
        requirement_id: str,
    ) -> Optional[FrameworkRequirement]:
        """Look up a specific requirement by framework and ID.

        Returns None if not found.
        """
        fw = SupportedFramework(framework) if isinstance(framework, str) else framework
        return self._index.get((fw, requirement_id))

    def map_requirement(
        self,
        framework: str | SupportedFramework,
        requirement_id: str,
        *,
        exclude_same_framework: bool = True,
    ) -> MappingResult:
        """Find equivalent requirements in other frameworks.

        Parameters
        ----------
        framework:
            Source framework name or enum value.
        requirement_id:
            ID of the requirement to map.
        exclude_same_framework:
            When True, results from the same framework are excluded.

        Returns
        -------
        MappingResult
            Matches sorted by descending similarity score.

        Raises
        ------
        KeyError
            When the source requirement is not found in the catalog.
        """
        fw = SupportedFramework(framework) if isinstance(framework, str) else framework
        source = self._index.get((fw, requirement_id))
        if source is None:
            raise KeyError(f"Requirement {requirement_id!r} not found in framework {fw.value!r}")

        matches: list[RequirementMatch] = []
        for (target_fw, _req_id), target_req in self._index.items():
            if exclude_same_framework and target_fw == fw:
                continue
            score = _jaccard_similarity(source.control_tags, target_req.control_tags)
            if score >= self._similarity_threshold:
                shared = source.control_tags & target_req.control_tags
                matches.append(
                    RequirementMatch(
                        framework=target_fw,
                        requirement_id=target_req.requirement_id,
                        requirement_name=target_req.name,
                        similarity_score=round(score, 4),
                        shared_tags=shared,
                    )
                )

        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        return MappingResult(
            source_framework=fw,
            source_requirement_id=requirement_id,
            source_requirement_name=source.name,
            matches=matches,
        )

    def map_all_requirements(
        self,
        framework: str | SupportedFramework,
    ) -> list[MappingResult]:
        """Map every requirement in a framework to other frameworks.

        Returns one MappingResult per requirement in the source framework.
        """
        fw = SupportedFramework(framework) if isinstance(framework, str) else framework
        results: list[MappingResult] = []
        for req in self._catalog.get(fw, []):
            result = self.map_requirement(fw, req.requirement_id)
            results.append(result)
        return results

    def list_requirements(
        self,
        framework: str | SupportedFramework,
    ) -> list[FrameworkRequirement]:
        """Return all requirements in a given framework."""
        fw = SupportedFramework(framework) if isinstance(framework, str) else framework
        return list(self._catalog.get(fw, []))

    def find_by_category(
        self,
        category: str,
        *,
        frameworks: Optional[list[SupportedFramework]] = None,
    ) -> list[FrameworkRequirement]:
        """Return all requirements matching a category across frameworks.

        Parameters
        ----------
        category:
            Category string to filter by (e.g. ``"transparency"``).
        frameworks:
            If provided, restrict search to these frameworks.
        """
        results: list[FrameworkRequirement] = []
        target_frameworks = frameworks or list(self._catalog.keys())
        for fw in target_frameworks:
            for req in self._catalog.get(fw, []):
                if req.category == category:
                    results.append(req)
        return results

    def find_by_tag(self, tag: str) -> list[FrameworkRequirement]:
        """Return all requirements whose control_tags contain the given tag."""
        return [
            req
            for req in self._index.values()
            if tag in req.control_tags
        ]

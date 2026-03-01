"""Cross-framework compliance gap analyser.

Analyses multiple :class:`~agent_gov.frameworks.base.FrameworkReport` objects
to surface overlapping requirements, unique gaps, unified remediation actions,
and an aggregate coverage score.

Example
-------
::

    from agent_gov.frameworks.eu_ai_act import EuAiActFramework
    from agent_gov.frameworks.iso_42001 import Iso42001Framework
    from agent_gov.frameworks.gap_analyzer import GapAnalyzer

    eu_report = EuAiActFramework().run_check({})
    iso_report = Iso42001Framework().run_check({})

    analyzer = GapAnalyzer()
    gap_report = analyzer.analyze([eu_report, iso_report])
    print(f"Coverage: {gap_report.coverage_score:.1%}")
    print(f"Overlap groups found: {len(gap_report.overlap_groups)}")
"""
from __future__ import annotations

from agent_gov.frameworks.base import FrameworkReport

try:
    from pydantic import BaseModel, Field
except ImportError as import_error:  # pragma: no cover
    raise ImportError(
        "pydantic is required for GapAnalyzer — install with: pip install pydantic>=2.0"
    ) from import_error


# ---------------------------------------------------------------------------
# Category-to-canonical-theme mapping used for overlap detection.
# Requirements from different frameworks that map to the same theme are grouped.
# ---------------------------------------------------------------------------

_CATEGORY_TO_THEME: dict[str, str] = {
    # Risk management
    "risk": "risk-management",
    "planning": "risk-management",
    # Data governance
    "data": "data-governance",
    # Transparency and explainability
    "transparency": "transparency",
    # Human oversight
    "oversight": "human-oversight",
    # Security and robustness
    "security": "security-robustness",
    # Governance, accountability, leadership
    "governance": "governance-accountability",
    "leadership": "governance-accountability",
    "context": "governance-accountability",
    "govern": "governance-accountability",
    # Documentation and logging
    "documentation": "documentation-logging",
    "logging": "documentation-logging",
    # Operations and monitoring
    "operations": "operations-monitoring",
    "monitoring": "operations-monitoring",
    "evaluation": "operations-monitoring",
    "measure": "operations-monitoring",
    "manage": "operations-monitoring",
    # Improvement
    "improvement": "improvement",
    # Support and workforce
    "support": "support-workforce",
    # Compliance and assessment
    "compliance": "compliance-assessment",
    "map": "compliance-assessment",
    # Prohibited / rights
    "prohibited": "prohibited-practices",
    "rights": "rights-impact",
}

_DEFAULT_THEME = "other"


def _resolve_theme(category: str) -> str:
    """Return the canonical theme string for a checklist item category."""
    return _CATEGORY_TO_THEME.get(category.lower(), _DEFAULT_THEME)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class OverlapGroup(BaseModel):
    """A group of requirements that share the same compliance theme.

    Attributes
    ----------
    theme:
        Canonical theme name (e.g. ``"risk-management"``).
    requirement_ids:
        List of requirement IDs across all analysed frameworks that fall
        under this theme.
    frameworks:
        Names of frameworks that contributed requirements to this group.
    """

    theme: str
    requirement_ids: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)


class RemediationItem(BaseModel):
    """A single deduplicated remediation action.

    Attributes
    ----------
    theme:
        The compliance theme this action addresses.
    failing_requirement_ids:
        Requirement IDs that are currently failing and require this action.
    action_description:
        Human-readable description of the corrective action to take.
    affected_frameworks:
        Frameworks in which failing requirements were found.
    """

    theme: str
    failing_requirement_ids: list[str] = Field(default_factory=list)
    action_description: str
    affected_frameworks: list[str] = Field(default_factory=list)


class GapAnalysisReport(BaseModel):
    """Aggregated cross-framework gap analysis report.

    Attributes
    ----------
    frameworks_analyzed:
        Names of the frameworks included in this analysis.
    total_requirements:
        Total number of requirements across all frameworks.
    passing_requirements:
        Number of requirements with status ``"pass"``.
    failing_requirements:
        Number of requirements with status ``"fail"`` or ``"unknown"``.
    overlap_groups:
        Requirement clusters grouped by compliance theme.
    unique_requirements:
        Per-framework dict of requirement IDs that appear only in that
        framework (no shared theme with any other framework).
    unified_remediation:
        Deduplicated list of remediation actions, one per failing theme.
    coverage_score:
        Fraction of all requirements that passed (0.0 to 1.0).
    """

    frameworks_analyzed: list[str] = Field(default_factory=list)
    total_requirements: int = 0
    passing_requirements: int = 0
    failing_requirements: int = 0
    overlap_groups: list[OverlapGroup] = Field(default_factory=list)
    unique_requirements: dict[str, list[str]] = Field(default_factory=dict)
    unified_remediation: list[RemediationItem] = Field(default_factory=list)
    coverage_score: float = 0.0


# ---------------------------------------------------------------------------
# GapAnalyzer
# ---------------------------------------------------------------------------


class GapAnalyzer:
    """Cross-framework compliance gap analyser.

    Accepts a list of :class:`~agent_gov.frameworks.base.FrameworkReport`
    objects and produces a :class:`GapAnalysisReport` identifying shared
    compliance themes, unique requirements, unified remediation actions, and
    an aggregate coverage score.
    """

    def analyze(self, reports: list[FrameworkReport]) -> GapAnalysisReport:
        """Analyse multiple framework reports for cross-framework gaps.

        Parameters
        ----------
        reports:
            List of :class:`~agent_gov.frameworks.base.FrameworkReport`
            objects to analyse.  An empty list returns an empty report.

        Returns
        -------
        GapAnalysisReport
            Report containing overlap groups, unique requirements per
            framework, unified remediation items, and coverage metrics.
        """
        if not reports:
            return GapAnalysisReport()

        framework_names = [report.framework for report in reports]

        # Build per-theme aggregation: theme -> list of (framework, item_id, status)
        theme_buckets: dict[str, list[tuple[str, str, str]]] = {}
        total_requirements = 0
        passing_requirements = 0

        for report in reports:
            for result in report.results:
                total_requirements += 1
                if result.status == "pass":
                    passing_requirements += 1

                theme = _resolve_theme(result.item.category)
                if theme not in theme_buckets:
                    theme_buckets[theme] = []
                theme_buckets[theme].append(
                    (report.framework, result.item.id, result.status)
                )

        failing_requirements = total_requirements - passing_requirements
        coverage_score = (
            passing_requirements / total_requirements if total_requirements > 0 else 0.0
        )

        # Build overlap groups: themes that appear in 2+ frameworks
        overlap_groups: list[OverlapGroup] = []
        theme_framework_counts: dict[str, set[str]] = {}
        for theme, entries in theme_buckets.items():
            framework_set: set[str] = {framework for framework, _, _ in entries}
            theme_framework_counts[theme] = framework_set

        for theme, entries in theme_buckets.items():
            framework_set = theme_framework_counts[theme]
            if len(framework_set) >= 2:
                requirement_ids = [item_id for _, item_id, _ in entries]
                overlap_groups.append(
                    OverlapGroup(
                        theme=theme,
                        requirement_ids=requirement_ids,
                        frameworks=sorted(framework_set),
                    )
                )

        # Build unique requirements per framework:
        # requirements whose theme appears in only one framework
        unique_requirements: dict[str, list[str]] = {name: [] for name in framework_names}
        for theme, entries in theme_buckets.items():
            framework_set = theme_framework_counts[theme]
            if len(framework_set) == 1:
                sole_framework = next(iter(framework_set))
                unique_ids = [item_id for _, item_id, _ in entries]
                unique_requirements[sole_framework].extend(unique_ids)

        # Build unified remediation list: one entry per failing theme
        unified_remediation: list[RemediationItem] = []
        failing_by_theme: dict[str, list[tuple[str, str]]] = {}
        for report in reports:
            for result in report.results:
                if result.status in ("fail", "unknown"):
                    theme = _resolve_theme(result.item.category)
                    if theme not in failing_by_theme:
                        failing_by_theme[theme] = []
                    failing_by_theme[theme].append(
                        (result.item.id, report.framework)
                    )

        for theme, failing_entries in sorted(failing_by_theme.items()):
            failing_ids = [item_id for item_id, _ in failing_entries]
            affected_frameworks = sorted(
                {framework for _, framework in failing_entries}
            )
            action_description = _build_action_description(theme)
            unified_remediation.append(
                RemediationItem(
                    theme=theme,
                    failing_requirement_ids=failing_ids,
                    action_description=action_description,
                    affected_frameworks=affected_frameworks,
                )
            )

        # Sort overlap groups by theme name for deterministic output
        overlap_groups.sort(key=lambda group: group.theme)

        return GapAnalysisReport(
            frameworks_analyzed=framework_names,
            total_requirements=total_requirements,
            passing_requirements=passing_requirements,
            failing_requirements=failing_requirements,
            overlap_groups=overlap_groups,
            unique_requirements=unique_requirements,
            unified_remediation=unified_remediation,
            coverage_score=coverage_score,
        )


# ---------------------------------------------------------------------------
# Remediation description helpers
# ---------------------------------------------------------------------------

_THEME_REMEDIATION_DESCRIPTIONS: dict[str, str] = {
    "risk-management": (
        "Establish or update a formal AI risk assessment and risk management system. "
        "Document identified risks, mitigation measures, and residual risk acceptance. "
        "Review and update the risk register at defined intervals."
    ),
    "data-governance": (
        "Implement data governance policies covering data quality, provenance, bias "
        "checks, and data minimisation for all AI training and operational datasets."
    ),
    "transparency": (
        "Ensure AI systems disclose their AI nature to users, provide interpretable "
        "outputs, and publish usage documentation and model cards as applicable."
    ),
    "human-oversight": (
        "Deploy human oversight mechanisms proportionate to system risk level, "
        "including override capabilities, monitoring dashboards, and review workflows."
    ),
    "security-robustness": (
        "Conduct adversarial robustness and cybersecurity testing. Implement "
        "monitoring for model drift, attacks, and operational anomalies."
    ),
    "governance-accountability": (
        "Define and communicate AI governance structures including ownership, "
        "accountability roles, escalation paths, and cross-functional review boards."
    ),
    "documentation-logging": (
        "Produce and maintain technical documentation and audit logs for all AI "
        "systems. Ensure logs capture sufficient detail for post-incident investigation."
    ),
    "operations-monitoring": (
        "Establish operational monitoring, performance evaluation, and incident "
        "reporting processes with defined KPIs, thresholds, and review cadences."
    ),
    "improvement": (
        "Implement a continual improvement process driven by audit findings, "
        "incident reviews, and management review outputs. Track corrective actions."
    ),
    "support-workforce": (
        "Ensure adequate resources, training, and communication for AI risk management "
        "roles. Document competency requirements and maintain training records."
    ),
    "compliance-assessment": (
        "Conduct formal compliance assessments and conformity evaluations for AI "
        "systems. Document assessment results and remediation timelines."
    ),
    "prohibited-practices": (
        "Audit all AI systems for prohibited practices including social scoring, "
        "exploitation of vulnerabilities, and unlawful biometric identification. "
        "Decommission or redesign any system in violation."
    ),
    "rights-impact": (
        "Conduct fundamental rights and societal impact assessments before deploying "
        "AI systems that affect individuals or groups, and document findings."
    ),
    "other": (
        "Review failing requirements and implement appropriate controls and "
        "documented evidence to bring each item into compliance."
    ),
}


def _build_action_description(theme: str) -> str:
    """Return a human-readable remediation description for the given theme."""
    return _THEME_REMEDIATION_DESCRIPTIONS.get(theme, _THEME_REMEDIATION_DESCRIPTIONS["other"])

"""ISO/IEC 42001:2023 AI Management System compliance framework.

Covers all clauses of ISO/IEC 42001:2023 — the international standard for
Artificial Intelligence Management Systems (AIMS).  Evidence keys use the
format ``"ISO42001_C<clause>_<item>"`` (e.g. ``"ISO42001_C4_1"``).

Evidence mapping
----------------
Pass each requirement ID as a key with a truthy value to mark it as satisfied,
or supply an ``"evidence"`` sub-key with a string explanation.

Example
-------
::

    from agent_gov.frameworks.iso_42001 import Iso42001Framework

    framework = Iso42001Framework()
    report = framework.run_check({
        "ISO42001_C4_1": {"status": "pass", "evidence": "Stakeholder analysis complete."},
        "ISO42001_C5_1": {"status": "pass", "evidence": "AI policy approved by board."},
        "ISO42001_C6_1": {"status": "fail", "evidence": "AI risk assessment not started."},
    })
    print(f"Score: {report.score_percent:.1f}%")
"""
from __future__ import annotations

from agent_gov.frameworks.base import (
    CheckResult,
    ChecklistItem,
    ComplianceFramework,
    FrameworkReport,
)
from agent_gov.frameworks.eu_ai_act import _resolve_evidence


class Iso42001Framework(ComplianceFramework):
    """ISO/IEC 42001:2023 AI Management System compliance checklist — 31 items.

    Covers Clauses 4 through 10 and Annex A AI-specific controls.

    Framework name: ``iso-42001``
    """

    name: str = "iso-42001"
    version: str = "2023"
    description: str = (
        "ISO/IEC 42001:2023 Artificial Intelligence Management System (AIMS) "
        "compliance checklist covering organisational context, leadership, "
        "planning, support, operations, performance evaluation, improvement, "
        "and Annex A AI-specific controls."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the full ISO/IEC 42001:2023 checklist (31 items)."""
        return [
            # ------------------------------------------------------------------
            # Clause 4 — Context of the Organisation
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C4_1",
                name="Understanding the Organisation and Its Context",
                description=(
                    "Clause 4.1: The organisation determines external and internal "
                    "issues relevant to its AI management system, including the "
                    "intended purpose of AI systems and the environment in which "
                    "they are deployed."
                ),
                category="context",
            ),
            ChecklistItem(
                id="ISO42001_C4_2",
                name="Understanding the Needs of Interested Parties",
                description=(
                    "Clause 4.2: The organisation determines the interested parties "
                    "relevant to the AIMS (e.g. employees, customers, regulators, "
                    "affected communities) and their needs and expectations."
                ),
                category="context",
            ),
            ChecklistItem(
                id="ISO42001_C4_3",
                name="Determining the Scope of the AIMS",
                description=(
                    "Clause 4.3: The organisation determines the boundaries and "
                    "applicability of the AIMS, considering external/internal issues, "
                    "requirements of interested parties, and AI systems in scope."
                ),
                category="context",
            ),
            ChecklistItem(
                id="ISO42001_C4_4",
                name="AI Management System Establishment",
                description=(
                    "Clause 4.4: The organisation establishes, implements, maintains, "
                    "and continually improves an AI management system in accordance "
                    "with the requirements of ISO/IEC 42001:2023."
                ),
                category="context",
            ),
            # ------------------------------------------------------------------
            # Clause 5 — Leadership
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C5_1",
                name="Leadership and Commitment",
                description=(
                    "Clause 5.1: Top management demonstrates leadership and commitment "
                    "to the AIMS by ensuring AI policy alignment with strategy, "
                    "integrating AIMS requirements into business processes, and "
                    "promoting continuous improvement."
                ),
                category="leadership",
            ),
            ChecklistItem(
                id="ISO42001_C5_2",
                name="AI Policy",
                description=(
                    "Clause 5.2: Top management establishes an AI policy appropriate "
                    "to the organisation's purpose, provides a framework for AI "
                    "objectives, includes commitments to satisfy applicable requirements, "
                    "and is communicated and available to interested parties."
                ),
                category="leadership",
            ),
            ChecklistItem(
                id="ISO42001_C5_3",
                name="Organisational Roles, Responsibilities, and Authorities",
                description=(
                    "Clause 5.3: Top management assigns and communicates responsibilities "
                    "and authorities for roles relevant to the AIMS, including roles "
                    "accountable for AI system performance and compliance."
                ),
                category="leadership",
            ),
            ChecklistItem(
                id="ISO42001_C5_4",
                name="Consultation and Participation of Workers",
                description=(
                    "Clause 5.4: The organisation establishes processes for consultation "
                    "and participation of workers at all applicable levels and functions "
                    "in the development and implementation of the AIMS."
                ),
                category="leadership",
            ),
            # ------------------------------------------------------------------
            # Clause 6 — Planning
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C6_1",
                name="AI Risk Assessment",
                description=(
                    "Clause 6.1: The organisation establishes, implements, and maintains "
                    "an AI risk assessment process that identifies risks and opportunities "
                    "associated with AI systems, considering their impact on individuals, "
                    "groups, and society."
                ),
                category="planning",
            ),
            ChecklistItem(
                id="ISO42001_C6_2",
                name="AI Objectives and Planning",
                description=(
                    "Clause 6.2: The organisation establishes AI objectives at relevant "
                    "functions and levels, consistent with the AI policy, measurable, "
                    "monitored, communicated, and updated as appropriate."
                ),
                category="planning",
            ),
            ChecklistItem(
                id="ISO42001_C6_3",
                name="Planning of Changes",
                description=(
                    "Clause 6.3: When the organisation determines the need for changes "
                    "to the AIMS, changes are carried out in a planned manner, considering "
                    "the purpose, consequences, availability of resources, and responsibilities."
                ),
                category="planning",
            ),
            ChecklistItem(
                id="ISO42001_C6_4",
                name="AI System Impact Assessment",
                description=(
                    "Clause 6.4 / Annex B: The organisation conducts AI system impact "
                    "assessments to evaluate potential impacts on individuals and society "
                    "prior to deployment and when significant changes occur."
                ),
                category="planning",
            ),
            # ------------------------------------------------------------------
            # Clause 7 — Support
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C7_1",
                name="Resources",
                description=(
                    "Clause 7.1: The organisation determines and provides resources "
                    "needed for the establishment, implementation, maintenance, and "
                    "continual improvement of the AIMS, including human, infrastructure, "
                    "and financial resources."
                ),
                category="support",
            ),
            ChecklistItem(
                id="ISO42001_C7_2",
                name="Competence",
                description=(
                    "Clause 7.2: The organisation determines necessary competences of "
                    "persons affecting AI performance, ensures those persons are competent, "
                    "takes actions to acquire competences, and retains documented evidence."
                ),
                category="support",
            ),
            ChecklistItem(
                id="ISO42001_C7_3",
                name="Awareness",
                description=(
                    "Clause 7.3: Persons doing work under the organisation's control "
                    "are aware of the AI policy, their contribution to AIMS effectiveness, "
                    "implications of not conforming, and responsible AI principles."
                ),
                category="support",
            ),
            ChecklistItem(
                id="ISO42001_C7_4",
                name="Communication",
                description=(
                    "Clause 7.4: The organisation determines the need for internal and "
                    "external communications relevant to the AIMS, including what, when, "
                    "with whom, and how to communicate."
                ),
                category="support",
            ),
            ChecklistItem(
                id="ISO42001_C7_5",
                name="Documented Information",
                description=(
                    "Clause 7.5: The organisation maintains documented information "
                    "required by ISO/IEC 42001:2023 and that it determines as necessary "
                    "for the effectiveness of the AIMS, with appropriate controls."
                ),
                category="support",
            ),
            # ------------------------------------------------------------------
            # Clause 8 — Operation
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C8_1",
                name="Operational Planning and Control",
                description=(
                    "Clause 8.1: The organisation plans, implements, controls, and "
                    "maintains processes needed to meet requirements for AI systems, "
                    "including criteria for processes and control of changes."
                ),
                category="operations",
            ),
            ChecklistItem(
                id="ISO42001_C8_2",
                name="AI Risk Treatment",
                description=(
                    "Clause 8.2: The organisation implements an AI risk treatment plan "
                    "selecting appropriate options to address identified AI risks, "
                    "implements those options, and retains documented evidence."
                ),
                category="operations",
            ),
            ChecklistItem(
                id="ISO42001_C8_3",
                name="AI System Development and Acquisition",
                description=(
                    "Clause 8.3: The organisation establishes controls for the "
                    "development or acquisition of AI systems covering requirements "
                    "specification, design, testing, and deployment stages."
                ),
                category="operations",
            ),
            ChecklistItem(
                id="ISO42001_C8_4",
                name="AI System Lifecycle Management",
                description=(
                    "Clause 8.4: The organisation manages AI systems throughout their "
                    "lifecycle including operation, monitoring, maintenance, and "
                    "decommissioning, with documented procedures for each phase."
                ),
                category="operations",
            ),
            # ------------------------------------------------------------------
            # Clause 9 — Performance Evaluation
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C9_1",
                name="Monitoring, Measurement, Analysis, and Evaluation",
                description=(
                    "Clause 9.1: The organisation determines what needs to be monitored "
                    "and measured, the methods, when to perform and evaluate, and "
                    "retains documented evidence of results."
                ),
                category="evaluation",
            ),
            ChecklistItem(
                id="ISO42001_C9_2",
                name="Internal Audit",
                description=(
                    "Clause 9.2: The organisation conducts internal audits at planned "
                    "intervals to provide information on whether the AIMS conforms to "
                    "requirements and is effectively implemented and maintained."
                ),
                category="evaluation",
            ),
            ChecklistItem(
                id="ISO42001_C9_3",
                name="Management Review",
                description=(
                    "Clause 9.3: Top management reviews the AIMS at planned intervals "
                    "to ensure its continuing suitability, adequacy, effectiveness, "
                    "and alignment with the strategic direction of the organisation."
                ),
                category="evaluation",
            ),
            ChecklistItem(
                id="ISO42001_C9_4",
                name="AI System Performance Review",
                description=(
                    "Clause 9.4: The organisation periodically reviews AI system "
                    "performance against defined objectives, bias metrics, fairness "
                    "criteria, and safety thresholds, with documented review records."
                ),
                category="evaluation",
            ),
            # ------------------------------------------------------------------
            # Clause 10 — Improvement
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_C10_1",
                name="Continual Improvement",
                description=(
                    "Clause 10.1: The organisation continually improves the suitability, "
                    "adequacy, and effectiveness of the AIMS using audit results, data "
                    "analysis, management review outputs, and corrective actions."
                ),
                category="improvement",
            ),
            ChecklistItem(
                id="ISO42001_C10_2",
                name="Nonconformity and Corrective Action",
                description=(
                    "Clause 10.2: When a nonconformity occurs, the organisation takes "
                    "action to control and correct it, evaluates the need for root-cause "
                    "action to prevent recurrence, and retains documented evidence."
                ),
                category="improvement",
            ),
            ChecklistItem(
                id="ISO42001_C10_3",
                name="Incident Management and Learning",
                description=(
                    "Clause 10.3: The organisation establishes processes to identify, "
                    "report, investigate, and learn from AI system incidents, near-misses, "
                    "and adverse outcomes to prevent recurrence."
                ),
                category="improvement",
            ),
            # ------------------------------------------------------------------
            # Annex A — AI-Specific Controls
            # ------------------------------------------------------------------
            ChecklistItem(
                id="ISO42001_A5",
                name="AI Policies and Responsible Use",
                description=(
                    "Annex A.5: The organisation defines and implements AI-specific "
                    "policies addressing responsible development, deployment, and use "
                    "of AI, including alignment with organisational values and ethics."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="ISO42001_A6",
                name="Internal Organisation for AI Governance",
                description=(
                    "Annex A.6: The organisation establishes internal roles and "
                    "governance structures specific to AI, including AI ownership, "
                    "cross-functional AI review boards, and escalation paths."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="ISO42001_A9",
                name="Human Oversight of AI Systems",
                description=(
                    "Annex A.9: The organisation implements human oversight mechanisms "
                    "for AI systems proportionate to their risk level, including review "
                    "of AI-generated outputs before consequential decisions."
                ),
                category="oversight",
            ),
            ChecklistItem(
                id="ISO42001_A10",
                name="AI Data Management Controls",
                description=(
                    "Annex A.10: The organisation implements controls for the quality, "
                    "integrity, provenance, and governance of data used in AI systems, "
                    "including data classification, labelling standards, and bias checks."
                ),
                category="data",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the ISO/IEC 42001:2023 checklist.

        Parameters
        ----------
        evidence:
            Dict keyed by requirement ID (e.g. ``"ISO42001_C4_1"``).
            Each value may be:

            - A mapping with ``"status"`` (``"pass"``/``"fail"``/``"unknown"``)
              and optional ``"evidence"`` string.
            - A plain truthy/falsy value (converted to ``"pass"``/``"fail"``).
            - Missing key -> ``"unknown"``.

        Returns
        -------
        FrameworkReport
        """
        results: list[CheckResult] = []
        for item in self.checklist():
            item_evidence = evidence.get(item.id)
            status, evidence_text = _resolve_evidence(item_evidence)
            results.append(CheckResult(item=item, status=status, evidence=evidence_text))

        return FrameworkReport(framework=self.name, results=results)

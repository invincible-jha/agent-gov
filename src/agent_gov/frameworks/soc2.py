"""SOC 2 Trust Services Criteria compliance framework — 5-item checklist.

Covers the five Trust Services Criteria (TSC) categories defined by the AICPA
as they apply to AI agent systems.

Evidence keys
-------------
- ``"CC6"`` — Security (Common Criteria 6: logical and physical access)
- ``"A1"`` — Availability
- ``"PI1"`` — Processing Integrity
- ``"C1"`` — Confidentiality
- ``"P1"`` — Privacy

Example
-------
::

    from agent_gov.frameworks.soc2 import Soc2Framework

    framework = Soc2Framework()
    report = framework.run_check({
        "CC6": {"status": "pass", "evidence": "MFA enforced, access logs reviewed monthly."},
        "A1": {"status": "pass", "evidence": "99.9% SLA with automated failover."},
        "PI1": {"status": "fail", "evidence": "No completeness checks on batch processing."},
        "C1": {"status": "pass", "evidence": "Data classified and encrypted at rest."},
        "P1": {"status": "unknown", "evidence": "Privacy assessment pending."},
    })
"""
from __future__ import annotations

from agent_gov.frameworks.base import (
    CheckResult,
    ChecklistItem,
    ComplianceFramework,
    FrameworkReport,
)
from agent_gov.frameworks.eu_ai_act import _resolve_evidence


class Soc2Framework(ComplianceFramework):
    """SOC 2 Trust Services Criteria — 5-item checklist.

    Framework name: ``soc2``
    """

    name: str = "soc2"
    version: str = "2017"
    description: str = (
        "SOC 2 Trust Services Criteria (AICPA) compliance checklist covering "
        "security, availability, processing integrity, confidentiality, and privacy."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the 5-item SOC 2 Trust Services Criteria checklist."""
        return [
            ChecklistItem(
                id="CC6",
                name="Security",
                description=(
                    "CC6 — Logical and Physical Access Controls: The system is protected "
                    "against unauthorised access using logical and physical access controls "
                    "including authentication, authorisation, and access monitoring."
                ),
                category="security",
            ),
            ChecklistItem(
                id="A1",
                name="Availability",
                description=(
                    "A1 — Availability: The system is available for operation and use "
                    "as committed or agreed, and meets defined performance and uptime "
                    "service level objectives."
                ),
                category="availability",
            ),
            ChecklistItem(
                id="PI1",
                name="Processing Integrity",
                description=(
                    "PI1 — Processing Integrity: System processing is complete, valid, "
                    "accurate, timely, and authorised to meet the entity's objectives."
                ),
                category="integrity",
            ),
            ChecklistItem(
                id="C1",
                name="Confidentiality",
                description=(
                    "C1 — Confidentiality: Information designated as confidential is "
                    "protected as committed or agreed through encryption, access controls, "
                    "and confidentiality agreements."
                ),
                category="confidentiality",
            ),
            ChecklistItem(
                id="P1",
                name="Privacy",
                description=(
                    "P1 — Privacy: Personal information is collected, used, retained, "
                    "disclosed, and disposed of in conformity with the commitments in the "
                    "entity's privacy notice."
                ),
                category="privacy",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the 5 SOC 2 Trust Services Criteria.

        Parameters
        ----------
        evidence:
            Dict keyed by criteria ID.  Same resolution rules as
            :meth:`~agent_gov.frameworks.eu_ai_act.EuAiActFramework.run_check`.

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

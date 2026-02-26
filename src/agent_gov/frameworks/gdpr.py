"""GDPR compliance framework — 7-item checklist.

Covers the seven data protection principles from Article 5 of the General
Data Protection Regulation (GDPR) as they apply to AI agent systems.

Evidence mapping
----------------
Use the principle IDs below as keys in the evidence dict:

- ``"P1"`` — Lawful basis
- ``"P2"`` — Purpose limitation
- ``"P3"`` — Data minimisation
- ``"P4"`` — Accuracy
- ``"P5"`` — Storage limitation
- ``"P6"`` — Integrity and confidentiality
- ``"P7"`` — Accountability

Example
-------
::

    from agent_gov.frameworks.gdpr import GdprFramework

    framework = GdprFramework()
    report = framework.run_check({
        "P1": {"status": "pass", "evidence": "Legitimate interest documented."},
        "P3": {"status": "pass", "evidence": "Only minimum required fields collected."},
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


class GdprFramework(ComplianceFramework):
    """GDPR Article 5 data protection principles — 7-item checklist.

    Framework name: ``gdpr``
    """

    name: str = "gdpr"
    version: str = "2018"
    description: str = (
        "General Data Protection Regulation (GDPR) compliance checklist "
        "covering the seven data protection principles of Article 5."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the 7-item GDPR checklist."""
        return [
            ChecklistItem(
                id="P1",
                name="Lawful Basis for Processing",
                description=(
                    "Article 5(1)(a): Personal data is processed lawfully, fairly, and "
                    "transparently.  A valid lawful basis (consent, contract, legal "
                    "obligation, vital interests, public task, or legitimate interests) "
                    "is identified and documented."
                ),
                category="lawfulness",
            ),
            ChecklistItem(
                id="P2",
                name="Purpose Limitation",
                description=(
                    "Article 5(1)(b): Personal data is collected for specified, explicit, "
                    "and legitimate purposes.  Data is not further processed in a manner "
                    "incompatible with those purposes."
                ),
                category="purpose",
            ),
            ChecklistItem(
                id="P3",
                name="Data Minimisation",
                description=(
                    "Article 5(1)(c): Personal data collected is adequate, relevant, and "
                    "limited to what is necessary in relation to the purposes for which it "
                    "is processed."
                ),
                category="data",
            ),
            ChecklistItem(
                id="P4",
                name="Accuracy",
                description=(
                    "Article 5(1)(d): Personal data is accurate and, where necessary, kept "
                    "up to date.  Every reasonable step is taken to ensure inaccurate data "
                    "is erased or corrected without delay."
                ),
                category="data",
            ),
            ChecklistItem(
                id="P5",
                name="Storage Limitation",
                description=(
                    "Article 5(1)(e): Personal data is kept in a form which permits "
                    "identification of data subjects for no longer than is necessary for "
                    "the purposes for which the data is processed."
                ),
                category="retention",
            ),
            ChecklistItem(
                id="P6",
                name="Integrity and Confidentiality",
                description=(
                    "Article 5(1)(f): Personal data is processed in a manner that ensures "
                    "appropriate security, including protection against unauthorised or "
                    "unlawful processing and against accidental loss, destruction, or "
                    "damage, using appropriate technical or organisational measures."
                ),
                category="security",
            ),
            ChecklistItem(
                id="P7",
                name="Accountability",
                description=(
                    "Article 5(2): The data controller is responsible for, and able to "
                    "demonstrate compliance with, the data protection principles."
                ),
                category="governance",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the 7 GDPR principle checklist items.

        Parameters
        ----------
        evidence:
            Dict keyed by principle ID.  Same resolution rules as
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

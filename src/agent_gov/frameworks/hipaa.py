"""HIPAA Security Rule compliance framework — 5-item checklist.

Covers the five core safeguard categories from the HIPAA Security Rule (45 CFR
Part 164) as they apply to AI systems that process protected health information
(PHI).

Evidence keys
-------------
- ``"SC1"`` — Access controls
- ``"SC2"`` — Audit controls
- ``"SC3"`` — Integrity
- ``"SC4"`` — Transmission security
- ``"SC5"`` — Business Associate Agreements (BAA)

Example
-------
::

    from agent_gov.frameworks.hipaa import HipaaFramework

    framework = HipaaFramework()
    report = framework.run_check({
        "SC1": {"status": "pass", "evidence": "Role-based access enforced via IAM."},
        "SC2": {"status": "pass", "evidence": "Audit logs retained 6 years."},
        "SC3": {"status": "fail", "evidence": "Checksums not implemented."},
        "SC4": {"status": "pass", "evidence": "TLS 1.3 enforced on all endpoints."},
        "SC5": {"status": "pass", "evidence": "BAA signed with all sub-processors."},
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


class HipaaFramework(ComplianceFramework):
    """HIPAA Security Rule safeguards — 5-item checklist.

    Framework name: ``hipaa``
    """

    name: str = "hipaa"
    version: str = "2013"
    description: str = (
        "HIPAA Security Rule (45 CFR Part 164) compliance checklist covering "
        "access controls, audit controls, integrity, transmission security, and BAAs."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the 5-item HIPAA Security Rule checklist."""
        return [
            ChecklistItem(
                id="SC1",
                name="Access Controls",
                description=(
                    "164.312(a)(1): Implement technical policies and procedures for "
                    "electronic information systems that maintain ePHI to allow access "
                    "only to those persons or software programs that have been granted "
                    "access rights."
                ),
                category="access",
            ),
            ChecklistItem(
                id="SC2",
                name="Audit Controls",
                description=(
                    "164.312(b): Implement hardware, software, and/or procedural "
                    "mechanisms that record and examine activity in information systems "
                    "that contain or use ePHI."
                ),
                category="audit",
            ),
            ChecklistItem(
                id="SC3",
                name="Integrity Controls",
                description=(
                    "164.312(c)(1): Implement policies and procedures to protect ePHI "
                    "from improper alteration or destruction, and authenticate that ePHI "
                    "has not been altered or destroyed in an unauthorised manner."
                ),
                category="integrity",
            ),
            ChecklistItem(
                id="SC4",
                name="Transmission Security",
                description=(
                    "164.312(e)(1): Implement technical security measures to guard "
                    "against unauthorised access to ePHI that is transmitted over an "
                    "electronic communications network."
                ),
                category="transmission",
            ),
            ChecklistItem(
                id="SC5",
                name="Business Associate Agreements",
                description=(
                    "164.308(b)(1): Obtain satisfactory assurances from business "
                    "associates that ePHI will be appropriately safeguarded through "
                    "signed Business Associate Agreements (BAAs)."
                ),
                category="governance",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the 5 HIPAA Security Rule checklist items.

        Parameters
        ----------
        evidence:
            Dict keyed by safeguard ID.  Same resolution rules as
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

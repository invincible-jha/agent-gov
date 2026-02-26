"""EU AI Act compliance framework — 8-item checklist.

Covers key articles from the EU Artificial Intelligence Act (2024) that are
most relevant to AI agent deployments.  Evidence keys are the article IDs
(``"A6"``, ``"A9"``, etc.).

Evidence mapping
----------------
Pass each article ID as a key with a truthy value to mark it as satisfied,
or supply an ``"evidence"`` sub-key with a string explanation.

Example
-------
::

    from agent_gov.frameworks.eu_ai_act import EuAiActFramework

    framework = EuAiActFramework()
    report = framework.run_check({
        "A6": {"status": "pass", "evidence": "System classified as limited risk."},
        "A9": {"status": "pass", "evidence": "Risk management plan documented."},
        "A10": {"status": "fail", "evidence": "Training data audit not completed."},
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


class EuAiActFramework(ComplianceFramework):
    """EU AI Act (2024) compliance checklist — 8 articles.

    Framework name: ``eu-ai-act``
    """

    name: str = "eu-ai-act"
    version: str = "2024"
    description: str = (
        "EU Artificial Intelligence Act (2024) compliance checklist covering "
        "risk classification, data governance, transparency, and oversight."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the 8-item EU AI Act checklist."""
        return [
            ChecklistItem(
                id="A6",
                name="Risk Classification",
                description=(
                    "Article 6: The AI system has been assessed and classified "
                    "according to the EU AI Act risk categories (unacceptable, high, "
                    "limited, minimal)."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A9",
                name="Risk Management System",
                description=(
                    "Article 9: A risk management system is established, implemented, "
                    "documented, and maintained for the lifecycle of the AI system."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A10",
                name="Data Governance",
                description=(
                    "Article 10: Training, validation, and testing datasets are subject "
                    "to data governance and management practices including bias examination."
                ),
                category="data",
            ),
            ChecklistItem(
                id="A13",
                name="Transparency and Information Provision",
                description=(
                    "Article 13: High-risk AI systems are designed to ensure sufficient "
                    "transparency for users to interpret outputs and use them appropriately."
                ),
                category="transparency",
            ),
            ChecklistItem(
                id="A14",
                name="Human Oversight",
                description=(
                    "Article 14: High-risk AI systems enable effective human oversight "
                    "during deployment, including the ability to override or halt the system."
                ),
                category="oversight",
            ),
            ChecklistItem(
                id="A15",
                name="Accuracy, Robustness, and Cybersecurity",
                description=(
                    "Article 15: High-risk AI systems achieve appropriate levels of "
                    "accuracy, robustness, and cybersecurity throughout their lifecycle."
                ),
                category="security",
            ),
            ChecklistItem(
                id="A52",
                name="Transparency Obligations for Certain AI Systems",
                description=(
                    "Article 52: AI systems intended to interact with natural persons "
                    "disclose that the user is interacting with an AI system."
                ),
                category="transparency",
            ),
            ChecklistItem(
                id="A60",
                name="EU Database Registration",
                description=(
                    "Article 60: High-risk AI systems are registered in the EU database "
                    "before being placed on the market or put into service."
                ),
                category="governance",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the 8 EU AI Act checklist items.

        Parameters
        ----------
        evidence:
            Dict keyed by article ID (``"A6"``, ``"A9"``, etc.).  Each value
            may be:
            - A mapping with ``"status"`` (``"pass"``/``"fail"``/``"unknown"``)
              and optional ``"evidence"`` string.
            - A plain truthy/falsy value (converted to ``"pass"``/``"fail"``).
            - Missing key → ``"unknown"``.

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


def _resolve_evidence(value: object) -> tuple[str, str]:
    """Resolve a raw evidence value to a (status, evidence_text) pair."""
    if value is None:
        return "unknown", "No evidence provided."
    if isinstance(value, dict):
        raw_status = str(value.get("status", "unknown")).lower()
        status = raw_status if raw_status in ("pass", "fail", "unknown") else "unknown"
        evidence_text = str(value.get("evidence", ""))
        return status, evidence_text
    # Treat truthy scalar as pass, falsy as fail
    return ("pass" if value else "fail"), str(value)

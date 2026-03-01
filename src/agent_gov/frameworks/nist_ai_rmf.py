"""NIST AI Risk Management Framework (AI RMF 1.0) compliance framework.

Covers all four core functions of the NIST AI RMF 1.0 (2023): GOVERN, MAP,
MEASURE, and MANAGE.  Evidence keys use the format
``"NIST_G<n>"``, ``"NIST_M<n>"``, ``"NIST_ME<n>"``, ``"NIST_MA<n>"``
for GOVERN, MAP, MEASURE, and MANAGE respectively.

Evidence mapping
----------------
Pass each function-item ID as a key with a truthy value to mark it as
satisfied, or supply an ``"evidence"`` sub-key with a string explanation.

Example
-------
::

    from agent_gov.frameworks.nist_ai_rmf import NistAiRmfFramework

    framework = NistAiRmfFramework()
    report = framework.run_check({
        "NIST_G1": {"status": "pass", "evidence": "AI governance policy in place."},
        "NIST_M1": {"status": "pass", "evidence": "AI use cases catalogued."},
        "NIST_ME1": {"status": "fail", "evidence": "Bias testing not completed."},
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


class NistAiRmfFramework(ComplianceFramework):
    """NIST AI Risk Management Framework 1.0 compliance checklist — 25 items.

    Covers the four core functions: GOVERN, MAP, MEASURE, and MANAGE.

    Framework name: ``nist-ai-rmf``
    """

    name: str = "nist-ai-rmf"
    version: str = "1.0"
    description: str = (
        "NIST AI Risk Management Framework (AI RMF 1.0, 2023) compliance checklist "
        "covering GOVERN (accountability and culture), MAP (risk identification), "
        "MEASURE (risk analysis and metrics), and MANAGE (risk treatment and response)."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the full NIST AI RMF 1.0 checklist (25 items)."""
        return [
            # ------------------------------------------------------------------
            # GOVERN — Cultivate organisational risk management culture (7 items)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="NIST_G1",
                name="AI Risk Management Policies Established",
                description=(
                    "GOVERN 1: Policies, processes, procedures, and practices are "
                    "established, communicated, and enforced across the organisation "
                    "that reflect the organisation's commitment to managing AI risk "
                    "throughout the AI lifecycle."
                ),
                category="govern",
            ),
            ChecklistItem(
                id="NIST_G2",
                name="Accountability Structures for AI Risk",
                description=(
                    "GOVERN 2: Accountability is defined for AI risk management roles "
                    "and responsibilities, including designated personnel or teams "
                    "accountable for AI risk outcomes and escalation paths."
                ),
                category="govern",
            ),
            ChecklistItem(
                id="NIST_G3",
                name="Risk Tolerance Defined",
                description=(
                    "GOVERN 3: Organisational risk tolerance for AI systems is "
                    "established, documented, and communicated.  Risk tolerance "
                    "thresholds are used to inform risk treatment decisions."
                ),
                category="govern",
            ),
            ChecklistItem(
                id="NIST_G4",
                name="Organisational Teams Empowered for AI Risk",
                description=(
                    "GOVERN 4: Organisational teams are empowered, informed, and "
                    "incentivised to manage AI risk.  Cross-disciplinary teams "
                    "participate in AI risk management activities."
                ),
                category="govern",
            ),
            ChecklistItem(
                id="NIST_G5",
                name="AI Risk Policies Consider Diversity and Inclusion",
                description=(
                    "GOVERN 5: Organisational policies and practices actively address "
                    "diversity, equity, inclusion, and accessibility concerns in AI "
                    "system design, development, deployment, and monitoring."
                ),
                category="govern",
            ),
            ChecklistItem(
                id="NIST_G6",
                name="Policies Include AI Supply Chain Risk",
                description=(
                    "GOVERN 6: Policies and procedures include AI supply chain and "
                    "third-party risk management, covering due diligence of AI "
                    "vendors, components, and pre-trained models used."
                ),
                category="govern",
            ),
            ChecklistItem(
                id="NIST_G7",
                name="AI Risk Management Workforce Training",
                description=(
                    "GOVERN 7: Personnel involved in AI development and deployment "
                    "receive training and education on AI risk management principles, "
                    "trustworthy AI characteristics, and their role-specific obligations."
                ),
                category="govern",
            ),
            # ------------------------------------------------------------------
            # MAP — Categorise and contextualise AI risk (5 items)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="NIST_M1",
                name="AI Use Context Documented",
                description=(
                    "MAP 1: The context in which AI systems are used is established "
                    "and documented, including intended purpose, expected benefits, "
                    "potential negative impacts, and the intended users and affected groups."
                ),
                category="map",
            ),
            ChecklistItem(
                id="NIST_M2",
                name="Stakeholder Identification and Engagement",
                description=(
                    "MAP 2: Scientific, technical, and organisational information "
                    "about AI risk and benefits is gathered from internal and external "
                    "stakeholders, including affected communities and domain experts."
                ),
                category="map",
            ),
            ChecklistItem(
                id="NIST_M3",
                name="AI Risk Categorisation",
                description=(
                    "MAP 3: AI risks and benefits are identified and categorised "
                    "considering technical, sociotechnical, and systemic dimensions "
                    "at all stages of the AI lifecycle."
                ),
                category="map",
            ),
            ChecklistItem(
                id="NIST_M4",
                name="Risks Prioritised by Likelihood and Magnitude",
                description=(
                    "MAP 4: Risks associated with specific AI systems are prioritised "
                    "based on their likelihood and potential magnitude of harm, "
                    "informed by risk tolerance and the deployment context."
                ),
                category="map",
            ),
            ChecklistItem(
                id="NIST_M5",
                name="AI Risk Identification Practices for Supply Chain",
                description=(
                    "MAP 5: Practices and personnel for AI risk identification and "
                    "management include supply chain components (third-party data, "
                    "models, and software), with appropriate due diligence applied."
                ),
                category="map",
            ),
            # ------------------------------------------------------------------
            # MEASURE — Analyse, assess, and benchmark AI risk (7 items)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="NIST_ME1",
                name="AI Risk Measurement Approaches Selected",
                description=(
                    "MEASURE 1: Approaches for measuring AI risks, benefits, and "
                    "trustworthy AI characteristics are defined and selected based "
                    "on scientific soundness, feasibility, and contextual relevance."
                ),
                category="measure",
            ),
            ChecklistItem(
                id="NIST_ME2",
                name="AI Risk Metrics Tracked",
                description=(
                    "MEASURE 2: AI risk metrics are established, tracked, and used "
                    "to inform risk management decisions.  Metrics cover technical "
                    "performance, fairness, robustness, and operational indicators."
                ),
                category="measure",
            ),
            ChecklistItem(
                id="NIST_ME3",
                name="Bias and Fairness Evaluated",
                description=(
                    "MEASURE 3: AI systems are evaluated for bias, fairness, and "
                    "equity impacts across affected demographic groups using "
                    "appropriate statistical and sociotechnical evaluation methods."
                ),
                category="measure",
            ),
            ChecklistItem(
                id="NIST_ME4",
                name="Privacy and Data Governance Risks Measured",
                description=(
                    "MEASURE 4: Privacy risks associated with AI data collection, "
                    "processing, and model outputs are identified, measured, and "
                    "documented, consistent with applicable privacy requirements."
                ),
                category="measure",
            ),
            ChecklistItem(
                id="NIST_ME5",
                name="Security and Adversarial Robustness Evaluated",
                description=(
                    "MEASURE 5: AI systems are tested and evaluated for security "
                    "vulnerabilities and adversarial robustness, including data "
                    "poisoning, model inversion, and evasion attack scenarios."
                ),
                category="measure",
            ),
            ChecklistItem(
                id="NIST_ME6",
                name="Explainability and Interpretability Assessed",
                description=(
                    "MEASURE 6: The explainability and interpretability of AI "
                    "systems are assessed relative to the deployment context, "
                    "and explanations are validated for accuracy and usefulness."
                ),
                category="measure",
            ),
            ChecklistItem(
                id="NIST_ME7",
                name="AI Risk Measurement Results Documented",
                description=(
                    "MEASURE 7: Results of AI risk measurements and evaluations "
                    "are documented, shared with relevant stakeholders, and used "
                    "to update risk assessments and inform MANAGE-phase actions."
                ),
                category="measure",
            ),
            # ------------------------------------------------------------------
            # MANAGE — Prioritise and address AI risk (6 items)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="NIST_MA1",
                name="Risk Treatment Plans Implemented",
                description=(
                    "MANAGE 1: AI risk treatment plans are developed and implemented "
                    "based on risk prioritisation, covering avoidance, transfer, "
                    "mitigation, and acceptance options with documented rationale."
                ),
                category="manage",
            ),
            ChecklistItem(
                id="NIST_MA2",
                name="AI Risk Response Mechanisms Deployed",
                description=(
                    "MANAGE 2: Mechanisms for responding to AI incidents, failures, "
                    "or unexpected behaviour are established, tested, and deployed "
                    "including escalation procedures and rollback capabilities."
                ),
                category="manage",
            ),
            ChecklistItem(
                id="NIST_MA3",
                name="Residual Risks and Trade-offs Communicated",
                description=(
                    "MANAGE 3: Residual AI risks and trade-offs after treatment are "
                    "communicated to decision-makers and relevant stakeholders, "
                    "enabling informed decisions about deployment and use."
                ),
                category="manage",
            ),
            ChecklistItem(
                id="NIST_MA4",
                name="Risk Monitoring and Re-evaluation Ongoing",
                description=(
                    "MANAGE 4: AI risks are monitored on an ongoing basis throughout "
                    "deployment, with trigger conditions defined for re-evaluation "
                    "and updates to risk assessments and treatment plans."
                ),
                category="manage",
            ),
            ChecklistItem(
                id="NIST_MA5",
                name="AI Decommissioning and Sunset Processes",
                description=(
                    "MANAGE 5: Processes for retiring or decommissioning AI systems "
                    "are established, including data retention and deletion, "
                    "stakeholder notification, and handover or replacement plans."
                ),
                category="manage",
            ),
            ChecklistItem(
                id="NIST_MA6",
                name="AI Incident Response and Learning",
                description=(
                    "MANAGE 6: The organisation responds to AI incidents in a timely "
                    "manner, documents root causes and corrective actions, and "
                    "integrates lessons learned into future risk management activities."
                ),
                category="manage",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the NIST AI RMF 1.0 checklist.

        Parameters
        ----------
        evidence:
            Dict keyed by function-item ID (e.g. ``"NIST_G1"``, ``"NIST_ME3"``).
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

"""EU AI Act compliance framework — 40+ item checklist.

Covers key articles from the EU Artificial Intelligence Act (2024) that are
most relevant to AI agent deployments.  Evidence keys are the article IDs
(e.g. ``"A5_1"``, ``"A6"``, ``"A9"``, etc.).

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
    """EU AI Act (2024) compliance checklist — 40+ articles.

    Covers Titles II through XII including prohibited practices, high-risk
    AI requirements, provider/deployer obligations, transparency obligations,
    governance structure, market surveillance, and penalties.

    Framework name: ``eu-ai-act``
    """

    name: str = "eu-ai-act"
    version: str = "2024"
    description: str = (
        "EU Artificial Intelligence Act (2024) compliance checklist covering "
        "prohibited practices, risk classification, data governance, technical "
        "documentation, transparency, human oversight, provider obligations, "
        "and governance structure."
    )

    def checklist(self) -> list[ChecklistItem]:
        """Return the full EU AI Act checklist (40+ items)."""
        return [
            # ------------------------------------------------------------------
            # Title II — Prohibited Practices (Art 5)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A5_1",
                name="Social Scoring Prohibition",
                description=(
                    "Article 5(1)(c): AI systems that evaluate or classify natural persons "
                    "based on their social behaviour or personal characteristics leading to "
                    "detrimental social scoring by public authorities are prohibited."
                ),
                category="prohibited",
            ),
            ChecklistItem(
                id="A5_2",
                name="Exploitation of Vulnerabilities Prohibition",
                description=(
                    "Article 5(1)(b): AI systems that exploit vulnerabilities of specific "
                    "groups of persons due to their age, disability, or social/economic "
                    "situation to materially distort their behaviour in a harmful manner "
                    "are prohibited."
                ),
                category="prohibited",
            ),
            ChecklistItem(
                id="A5_3",
                name="Real-Time Biometric Identification Limits",
                description=(
                    "Article 5(1)(d): Real-time remote biometric identification systems "
                    "in publicly accessible spaces for law enforcement purposes are "
                    "prohibited except in narrowly defined circumstances with prior "
                    "authorisation and strict conditions."
                ),
                category="prohibited",
            ),
            ChecklistItem(
                id="A5_4",
                name="Emotion Recognition in Workplace and Education Prohibition",
                description=(
                    "Article 5(1)(f): AI systems that infer emotions of natural persons "
                    "in the areas of workplace and educational institutions are prohibited, "
                    "except for safety or medical purposes."
                ),
                category="prohibited",
            ),
            # ------------------------------------------------------------------
            # Title III Chapter 1 — High-Risk Classification (Art 6-8)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A6",
                name="Risk Classification",
                description=(
                    "Article 6: The AI system has been assessed and classified "
                    "according to the EU AI Act risk categories (unacceptable, high, "
                    "limited, minimal) using the criteria in Annex II and III."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A7",
                name="Stand-Alone High-Risk AI Determination",
                description=(
                    "Article 7: Where the AI system is a stand-alone high-risk system "
                    "per Annex III, a formal determination has been made and documented "
                    "confirming it falls within one of the listed high-risk categories."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A8",
                name="Compliance with Requirements for High-Risk AI",
                description=(
                    "Article 8: High-risk AI systems comply with all requirements set "
                    "out in Chapter 2 of Title III, and evidence of compliance is "
                    "documented and maintained throughout the system lifecycle."
                ),
                category="risk",
            ),
            # ------------------------------------------------------------------
            # Title III Chapter 2 — Requirements (Art 9-15)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A9",
                name="Risk Management System",
                description=(
                    "Article 9: A risk management system is established, implemented, "
                    "documented, and maintained for the lifecycle of the AI system. "
                    "It identifies and analyses known and foreseeable risks and adopts "
                    "risk management measures."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A10",
                name="Data and Data Governance",
                description=(
                    "Article 10: Training, validation, and testing datasets are subject "
                    "to data governance and management practices including bias examination, "
                    "relevance checks, and appropriate data collection processes."
                ),
                category="data",
            ),
            ChecklistItem(
                id="A11",
                name="Technical Documentation",
                description=(
                    "Article 11: Technical documentation is drawn up before the high-risk "
                    "AI system is placed on the market or put into service. Documentation "
                    "covers system purpose, design, development, and performance in "
                    "accordance with Annex IV."
                ),
                category="documentation",
            ),
            ChecklistItem(
                id="A12",
                name="Record-Keeping and Logging",
                description=(
                    "Article 12: High-risk AI systems have logging capabilities enabling "
                    "automatic recording of events throughout the lifecycle. Logs allow "
                    "post-market monitoring and investigation of incidents."
                ),
                category="logging",
            ),
            ChecklistItem(
                id="A13",
                name="Transparency and Information Provision",
                description=(
                    "Article 13: High-risk AI systems are designed to ensure sufficient "
                    "transparency for deployers to interpret outputs and use them "
                    "appropriately. Instructions for use are provided in clear language."
                ),
                category="transparency",
            ),
            ChecklistItem(
                id="A14",
                name="Human Oversight",
                description=(
                    "Article 14: High-risk AI systems enable effective human oversight "
                    "during deployment, including the ability to understand capabilities "
                    "and limitations, override or halt the system, and avoid over-reliance."
                ),
                category="oversight",
            ),
            ChecklistItem(
                id="A15",
                name="Accuracy, Robustness, and Cybersecurity",
                description=(
                    "Article 15: High-risk AI systems achieve appropriate levels of "
                    "accuracy, robustness, and cybersecurity throughout their lifecycle. "
                    "Systems are resilient against errors, faults, and adversarial attacks."
                ),
                category="security",
            ),
            # ------------------------------------------------------------------
            # Title III Chapter 3 — Provider and Deployer Obligations (Art 16-29)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A16",
                name="Provider Obligations",
                description=(
                    "Article 16: Providers of high-risk AI systems fulfil obligations "
                    "including ensuring compliance, affixing CE marking, registration in "
                    "the EU database, and taking corrective actions when necessary."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A17",
                name="Quality Management System",
                description=(
                    "Article 17: Providers implement a quality management system "
                    "covering compliance strategy, design development and quality "
                    "checks, data management practices, and post-market monitoring."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A22",
                name="Authorised Representative Obligations",
                description=(
                    "Article 22: Where the provider is established outside the EU, "
                    "an authorised representative established in the EU is designated "
                    "and mandated by written mandate to act on the provider's behalf."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A26",
                name="Deployer Obligations",
                description=(
                    "Article 26: Deployers of high-risk AI systems implement appropriate "
                    "technical and organisational measures, assign human oversight to "
                    "qualified persons, and inform affected persons where required."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A27",
                name="Fundamental Rights Impact Assessment",
                description=(
                    "Article 27: Deployers that are bodies governed by public law or "
                    "private operators providing public services conduct a fundamental "
                    "rights impact assessment before deploying a high-risk AI system."
                ),
                category="rights",
            ),
            ChecklistItem(
                id="A29",
                name="Deployer Monitoring Obligations",
                description=(
                    "Article 29: Deployers monitor the operation of the high-risk AI "
                    "system based on instructions for use and inform providers of any "
                    "serious incidents or malfunctions without delay."
                ),
                category="oversight",
            ),
            # ------------------------------------------------------------------
            # Title IV — Transparency Obligations (Art 50-56)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A50",
                name="Transparency for GPAI Interactions",
                description=(
                    "Article 50: Providers of AI systems intended to interact with "
                    "natural persons ensure those persons are informed they are "
                    "interacting with an AI system, unless this is obvious from context."
                ),
                category="transparency",
            ),
            ChecklistItem(
                id="A52",
                name="Deepfake Labelling",
                description=(
                    "Article 52: AI systems that generate or manipulate image, audio, "
                    "or video content constituting deepfakes label the content as "
                    "artificially generated or manipulated in a machine-readable format."
                ),
                category="transparency",
            ),
            ChecklistItem(
                id="A53",
                name="GPAI Model Transparency",
                description=(
                    "Article 53: Providers of general-purpose AI models maintain "
                    "technical documentation, provide information to downstream "
                    "providers, and comply with copyright law including summary "
                    "of training data used."
                ),
                category="transparency",
            ),
            ChecklistItem(
                id="A55",
                name="Systemic Risk GPAI Obligations",
                description=(
                    "Article 55: Providers of general-purpose AI models with systemic "
                    "risk perform model evaluations, assess and mitigate systemic risks, "
                    "report serious incidents, and ensure adequate cybersecurity protection."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A56",
                name="Codes of Practice",
                description=(
                    "Article 56: Providers of general-purpose AI models and models with "
                    "systemic risk participate in or adhere to codes of practice drawn "
                    "up by the AI Office until harmonised standards are published."
                ),
                category="governance",
            ),
            # ------------------------------------------------------------------
            # Title V — General Purpose AI Models (Art 51-56 governance)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A51",
                name="GPAI Model Classification",
                description=(
                    "Article 51: Providers determine whether their general-purpose AI "
                    "model presents systemic risk using the computational threshold of "
                    "10^25 FLOPs or by Commission designation, and document the determination."
                ),
                category="risk",
            ),
            ChecklistItem(
                id="A54",
                name="GPAI Provider Cooperation with AI Office",
                description=(
                    "Article 54: Providers of general-purpose AI models cooperate with "
                    "the AI Office upon request, providing documentation, access, and "
                    "information needed for evaluation and monitoring."
                ),
                category="governance",
            ),
            # ------------------------------------------------------------------
            # Title VI — Governance (Art 57-68)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A57",
                name="AI Office Governance",
                description=(
                    "Article 57: The organisation monitors and tracks the EU AI Office "
                    "guidelines, opinions, and decisions relevant to its AI systems "
                    "and updates compliance practices accordingly."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A59",
                name="National Competent Authority Designation",
                description=(
                    "Article 59: The organisation identifies the national competent "
                    "authority responsible for supervising its AI systems and "
                    "establishes a point of contact for regulatory enquiries."
                ),
                category="governance",
            ),
            # ------------------------------------------------------------------
            # Title VII — EU Database for High-Risk AI (Art 60-71)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A60",
                name="EU Database Registration",
                description=(
                    "Article 60: High-risk AI systems are registered in the EU database "
                    "before being placed on the market or put into service, and "
                    "registration information is kept accurate and up to date."
                ),
                category="governance",
            ),
            # ------------------------------------------------------------------
            # Title VIII — Post-Market Monitoring (Art 72-74)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A72",
                name="Post-Market Monitoring System",
                description=(
                    "Article 72: Providers establish and document a post-market "
                    "monitoring system proportionate to the nature of the AI technology "
                    "and the risks of the high-risk AI system."
                ),
                category="monitoring",
            ),
            ChecklistItem(
                id="A73",
                name="Serious Incident Reporting",
                description=(
                    "Article 73: Providers report serious incidents to the market "
                    "surveillance authority of the Member State where the incident "
                    "occurred without undue delay and no later than 15 days after "
                    "becoming aware."
                ),
                category="monitoring",
            ),
            # ------------------------------------------------------------------
            # Title IX — Market Surveillance (Art 74-80)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A74",
                name="Market Surveillance and Control",
                description=(
                    "Article 74: The organisation cooperates with market surveillance "
                    "authorities, provides requested documentation and access to systems, "
                    "and complies with corrective actions ordered."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A79",
                name="Corrective Actions and Withdrawal",
                description=(
                    "Article 79: Providers and deployers take corrective actions to "
                    "bring non-conforming AI systems into conformity, withdraw or recall "
                    "systems where necessary, and inform distributors and deployers."
                ),
                category="governance",
            ),
            # ------------------------------------------------------------------
            # Title X — Confidentiality and Penalties (Art 78-99)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A78",
                name="Confidentiality Obligations",
                description=(
                    "Article 78: All parties involved in applying the Regulation "
                    "respect the confidentiality of information and data obtained "
                    "in carrying out their tasks and activities."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A99",
                name="Penalties Framework Awareness",
                description=(
                    "Article 99: The organisation is aware of the penalty framework "
                    "including fines up to EUR 35M or 7% of annual global turnover "
                    "for prohibited-practice violations, and has controls to avoid "
                    "prohibited uses."
                ),
                category="governance",
            ),
            # ------------------------------------------------------------------
            # Title XI — Delegation and Implementing Acts (Art 97-101)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A97",
                name="Conformity Assessment Procedure",
                description=(
                    "Article 97: High-risk AI systems undergo the applicable conformity "
                    "assessment procedure before being placed on the market, with "
                    "involvement of a notified body where required."
                ),
                category="compliance",
            ),
            # ------------------------------------------------------------------
            # Title XII — Final Provisions (Art 102-113)
            # ------------------------------------------------------------------
            ChecklistItem(
                id="A101",
                name="AI Sandboxes Participation",
                description=(
                    "Article 101: Where applicable, the organisation participates in "
                    "regulatory AI sandboxes established by competent authorities to "
                    "foster innovation while ensuring compliance."
                ),
                category="governance",
            ),
            ChecklistItem(
                id="A103",
                name="CE Marking and Declaration of Conformity",
                description=(
                    "Article 103: High-risk AI systems bear the CE conformity marking "
                    "and an EU declaration of conformity is drawn up confirming "
                    "compliance with all applicable requirements."
                ),
                category="compliance",
            ),
            ChecklistItem(
                id="A113",
                name="Transition and Applicability Timeline",
                description=(
                    "Article 113: The organisation has mapped the applicability timeline "
                    "for each AI system category — prohibited practices prohibited 6 months "
                    "after entry into force, GPAI provisions 12 months, high-risk AI "
                    "requirements 24 months."
                ),
                category="governance",
            ),
        ]

    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against the full EU AI Act checklist.

        Parameters
        ----------
        evidence:
            Dict keyed by article ID (``"A5_1"``, ``"A6"``, ``"A9"``, etc.).
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

"""Compliance requirement catalogues for EU AI Act, GDPR, and HIPAA.

Each :class:`~agent_gov.compliance_cost.calculator.ComplianceRequirement`
entry records:
- ``framework``: which regulation it belongs to.
- ``requirement_id``: short reference identifier.
- ``description``: plain-language description.
- ``automation_level``: commodity label (fully_automated / semi_automated / manual).
- ``estimated_hours_manual``: analyst-hours when done entirely by hand.
- ``estimated_hours_automated``: analyst-hours when tooling handles it.

Hour estimates are generic industry benchmarks — they are NOT derived
from any proprietary analysis.  Adjust them to your organisation's
baseline via :class:`~agent_gov.compliance_cost.calculator.ComplianceCostCalculator`.
"""
from __future__ import annotations

from agent_gov.compliance_cost.calculator import ComplianceRequirement

# ---------------------------------------------------------------------------
# EU AI Act (2024)
# ---------------------------------------------------------------------------

EU_AI_ACT_REQUIREMENTS: list[ComplianceRequirement] = [
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A6_risk_classification",
        description="Article 6: Classify the AI system under the risk taxonomy.",
        automation_level="semi_automated",
        estimated_hours_manual=40.0,
        estimated_hours_automated=8.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A9_risk_mgmt_system",
        description="Article 9: Establish and maintain a risk management system.",
        automation_level="semi_automated",
        estimated_hours_manual=80.0,
        estimated_hours_automated=20.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A10_data_governance",
        description="Article 10: Data governance — training, validation, testing datasets.",
        automation_level="semi_automated",
        estimated_hours_manual=60.0,
        estimated_hours_automated=15.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A11_technical_documentation",
        description="Article 11: Maintain technical documentation before market placement.",
        automation_level="fully_automated",
        estimated_hours_manual=30.0,
        estimated_hours_automated=2.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A12_record_keeping",
        description="Article 12: Automatic logging of events throughout system lifetime.",
        automation_level="fully_automated",
        estimated_hours_manual=20.0,
        estimated_hours_automated=1.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A13_transparency",
        description="Article 13: Transparency — ensure users understand AI outputs.",
        automation_level="semi_automated",
        estimated_hours_manual=25.0,
        estimated_hours_automated=5.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A14_human_oversight",
        description="Article 14: Enable effective human oversight during operation.",
        automation_level="semi_automated",
        estimated_hours_manual=35.0,
        estimated_hours_automated=10.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A15_accuracy_robustness",
        description="Article 15: Accuracy, robustness, and cybersecurity requirements.",
        automation_level="semi_automated",
        estimated_hours_manual=50.0,
        estimated_hours_automated=12.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A16_conformity_assessment",
        description="Article 16: Provider obligations — conformity assessment procedures.",
        automation_level="manual",
        estimated_hours_manual=60.0,
        estimated_hours_automated=20.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A52_ai_disclosure",
        description="Article 52: Disclose that users are interacting with an AI system.",
        automation_level="fully_automated",
        estimated_hours_manual=10.0,
        estimated_hours_automated=0.5,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A60_eu_database_registration",
        description="Article 60: Register high-risk AI systems in the EU database.",
        automation_level="manual",
        estimated_hours_manual=15.0,
        estimated_hours_automated=5.0,
    ),
    ComplianceRequirement(
        framework="eu_ai_act",
        requirement_id="A72_post_market_monitoring",
        description="Article 72: Establish post-market monitoring system.",
        automation_level="semi_automated",
        estimated_hours_manual=40.0,
        estimated_hours_automated=8.0,
    ),
]

# ---------------------------------------------------------------------------
# GDPR (2018)
# ---------------------------------------------------------------------------

GDPR_REQUIREMENTS: list[ComplianceRequirement] = [
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A5_lawfulness",
        description="Article 5: Ensure lawfulness, fairness, and transparency of processing.",
        automation_level="semi_automated",
        estimated_hours_manual=30.0,
        estimated_hours_automated=6.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A6_legal_basis",
        description="Article 6: Identify and document legal basis for each processing activity.",
        automation_level="manual",
        estimated_hours_manual=20.0,
        estimated_hours_automated=8.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A13_14_privacy_notice",
        description="Articles 13/14: Provide privacy notices to data subjects.",
        automation_level="semi_automated",
        estimated_hours_manual=15.0,
        estimated_hours_automated=3.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A17_right_erasure",
        description="Article 17: Implement right to erasure (right to be forgotten).",
        automation_level="semi_automated",
        estimated_hours_manual=40.0,
        estimated_hours_automated=10.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A20_data_portability",
        description="Article 20: Implement data portability for data subjects.",
        automation_level="semi_automated",
        estimated_hours_manual=30.0,
        estimated_hours_automated=8.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A25_privacy_by_design",
        description="Article 25: Implement privacy by design and by default.",
        automation_level="manual",
        estimated_hours_manual=60.0,
        estimated_hours_automated=20.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A30_ropa",
        description="Article 30: Maintain Records of Processing Activities (RoPA).",
        automation_level="fully_automated",
        estimated_hours_manual=25.0,
        estimated_hours_automated=2.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A32_security_measures",
        description="Article 32: Implement appropriate technical and organisational security measures.",
        automation_level="semi_automated",
        estimated_hours_manual=50.0,
        estimated_hours_automated=12.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A33_breach_notification",
        description="Article 33: 72-hour data breach notification to supervisory authority.",
        automation_level="semi_automated",
        estimated_hours_manual=20.0,
        estimated_hours_automated=4.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A35_dpia",
        description="Article 35: Conduct Data Protection Impact Assessment (DPIA) for high-risk processing.",
        automation_level="manual",
        estimated_hours_manual=80.0,
        estimated_hours_automated=25.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A37_dpo",
        description="Article 37: Appoint a Data Protection Officer where required.",
        automation_level="manual",
        estimated_hours_manual=10.0,
        estimated_hours_automated=10.0,
    ),
    ComplianceRequirement(
        framework="gdpr",
        requirement_id="A44_transfers",
        description="Article 44: Ensure adequate safeguards for international data transfers.",
        automation_level="manual",
        estimated_hours_manual=40.0,
        estimated_hours_automated=15.0,
    ),
]

# ---------------------------------------------------------------------------
# HIPAA (45 CFR Parts 160 and 164)
# ---------------------------------------------------------------------------

HIPAA_REQUIREMENTS: list[ComplianceRequirement] = [
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_308a_risk_analysis",
        description="164.308(a)(1)(ii)(A): Conduct accurate and thorough risk analysis.",
        automation_level="semi_automated",
        estimated_hours_manual=60.0,
        estimated_hours_automated=15.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_308a_workforce_training",
        description="164.308(a)(5): Implement security awareness and training program.",
        automation_level="semi_automated",
        estimated_hours_manual=40.0,
        estimated_hours_automated=10.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_308a_access_management",
        description="164.308(a)(4): Implement role-based access management for PHI.",
        automation_level="fully_automated",
        estimated_hours_manual=30.0,
        estimated_hours_automated=3.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_310_physical_safeguards",
        description="164.310: Physical safeguards for workstations accessing PHI.",
        automation_level="manual",
        estimated_hours_manual=20.0,
        estimated_hours_automated=8.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_312_access_control",
        description="164.312(a)(1): Technical access control — unique user identification.",
        automation_level="fully_automated",
        estimated_hours_manual=20.0,
        estimated_hours_automated=1.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_312_audit_controls",
        description="164.312(b): Audit controls — hardware, software, and procedural mechanisms.",
        automation_level="fully_automated",
        estimated_hours_manual=25.0,
        estimated_hours_automated=2.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_312_integrity",
        description="164.312(c)(1): Protect PHI from improper alteration or destruction.",
        automation_level="semi_automated",
        estimated_hours_manual=30.0,
        estimated_hours_automated=6.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_312_encryption",
        description="164.312(e)(2)(ii): Encryption of PHI in transit and at rest.",
        automation_level="fully_automated",
        estimated_hours_manual=20.0,
        estimated_hours_automated=1.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_314_baa",
        description="164.314(a): Business Associate Agreements with all covered vendors.",
        automation_level="manual",
        estimated_hours_manual=30.0,
        estimated_hours_automated=10.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_400_breach_notification",
        description="164.400: Breach notification — notify affected individuals within 60 days.",
        automation_level="semi_automated",
        estimated_hours_manual=20.0,
        estimated_hours_automated=4.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_520_notice_privacy",
        description="164.520: Notice of Privacy Practices to patients.",
        automation_level="semi_automated",
        estimated_hours_manual=15.0,
        estimated_hours_automated=3.0,
    ),
    ComplianceRequirement(
        framework="hipaa",
        requirement_id="164_524_access_phi",
        description="164.524: Individual right to access their PHI within 30 days.",
        automation_level="semi_automated",
        estimated_hours_manual=25.0,
        estimated_hours_automated=5.0,
    ),
]

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

FRAMEWORK_REGISTRY: dict[str, list[ComplianceRequirement]] = {
    "eu_ai_act": EU_AI_ACT_REQUIREMENTS,
    "gdpr": GDPR_REQUIREMENTS,
    "hipaa": HIPAA_REQUIREMENTS,
}


def get_requirements(framework: str) -> list[ComplianceRequirement]:
    """Return the requirement list for the given framework name.

    Parameters
    ----------
    framework:
        One of ``"eu_ai_act"``, ``"gdpr"``, ``"hipaa"``.

    Returns
    -------
    list[ComplianceRequirement]

    Raises
    ------
    KeyError
        If *framework* is not registered.
    """
    if framework not in FRAMEWORK_REGISTRY:
        available = ", ".join(sorted(FRAMEWORK_REGISTRY.keys()))
        raise KeyError(f"Unknown framework {framework!r}. Available: {available}")
    return list(FRAMEWORK_REGISTRY[framework])


def list_frameworks() -> list[str]:
    """Return sorted list of registered framework names."""
    return sorted(FRAMEWORK_REGISTRY.keys())


__all__ = [
    "EU_AI_ACT_REQUIREMENTS",
    "FRAMEWORK_REGISTRY",
    "GDPR_REQUIREMENTS",
    "HIPAA_REQUIREMENTS",
    "get_requirements",
    "list_frameworks",
]

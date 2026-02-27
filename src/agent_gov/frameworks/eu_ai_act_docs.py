"""EU AI Act Annex IV technical documentation generator.

Provides a structured dataclass representing the full Annex IV technical
documentation package required for high-risk AI systems under
Regulation (EU) 2024/1689.

The documentation package can be exported to Markdown (human-readable) and
JSON (machine-readable) formats suitable for regulatory submissions.

Example
-------
::

    from agent_gov.frameworks.eu_ai_act_docs import AnnexIVDocumentation

    doc = AnnexIVDocumentation(
        system_name="CreditScore v2",
        system_version="2.1.0",
        provider_name="Acme Finance GmbH",
        intended_purpose="Automated creditworthiness assessment.",
        system_description="ML model trained on loan repayment data.",
        known_limitations=["Only validated for EU residents"],
    )
    files = doc.export("/tmp/annex-iv-docs/")
    print(files)  # ['.../annex-iv-technical-documentation.md', '.../annex-iv-data.json']
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AnnexIVDocumentation:
    """EU AI Act Annex IV technical documentation package.

    Each field corresponds to a section of Annex IV of Regulation (EU) 2024/1689.
    All fields have sensible defaults so the dataclass can be constructed
    incrementally and exported at any stage.

    Attributes
    ----------
    system_name:
        Name of the AI system (Annex IV(1)).
    system_version:
        Version identifier of the AI system.
    provider_name:
        Name of the provider organisation.
    intended_purpose:
        Clear statement of the intended purpose (Annex IV(1)).
    system_description:
        General description of the AI system, including its inputs, outputs,
        and functional logic (Annex IV(1)).
    design_specifications:
        Design choices, assumptions, and constraints (Annex IV(2)).
    development_methodology:
        Description of the development process and methodology (Annex IV(2)).
    validation_procedures:
        Procedures used to validate the system before deployment (Annex IV(2)).
    human_oversight_measures:
        Measures enabling human oversight during operation (Annex IV(3)).
    shutdown_procedures:
        Procedures for overriding or halting the system (Annex IV(3)).
    risk_assessment:
        Description of the risk assessment performed (Annex IV(4)).
    risk_mitigation_measures:
        Measures taken to mitigate identified risks (Annex IV(4)).
    training_data_description:
        Description of training datasets, their sources, and characteristics
        (Annex IV(5)).
    data_preparation_methods:
        Methods used to prepare and pre-process training data (Annex IV(5)).
    data_quality_metrics:
        Metrics used to assess data quality (Annex IV(5)).
    performance_metrics:
        Key performance metrics and their values (Annex IV(6)).
    testing_results:
        Results of performance and accuracy testing (Annex IV(6)).
    known_limitations:
        List of known limitations and failure modes (Annex IV(6)).
    cybersecurity_assessment:
        Assessment of cybersecurity risks and attack surfaces (Annex IV(7)).
    robustness_measures:
        Measures taken to ensure robustness against adversarial inputs
        (Annex IV(7)).
    security_scan_results:
        Results of security scanning tools and penetration tests (Annex IV(7)).
    generated_at:
        ISO 8601 UTC timestamp when this documentation was generated.
    eu_ai_act_version:
        The version of the EU AI Act regulation this documentation conforms to.
    """

    # Annex IV(1) — General description
    system_name: str = ""
    system_version: str = ""
    provider_name: str = ""
    intended_purpose: str = ""
    system_description: str = ""

    # Annex IV(2) — Development process
    design_specifications: str = ""
    development_methodology: str = ""
    validation_procedures: str = ""

    # Annex IV(3) — Monitoring and control
    human_oversight_measures: str = ""
    shutdown_procedures: str = ""

    # Annex IV(4) — Risk management
    risk_assessment: str = ""
    risk_mitigation_measures: str = ""

    # Annex IV(5) — Data governance
    training_data_description: str = ""
    data_preparation_methods: str = ""
    data_quality_metrics: str = ""

    # Annex IV(6) — Performance
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    testing_results: dict[str, Any] = field(default_factory=dict)
    known_limitations: list[str] = field(default_factory=list)

    # Annex IV(7) — Cybersecurity
    cybersecurity_assessment: str = ""
    robustness_measures: str = ""
    security_scan_results: dict[str, Any] = field(default_factory=dict)

    # Metadata
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    eu_ai_act_version: str = "Regulation (EU) 2024/1689"

    def to_markdown(self) -> str:
        """Generate a Markdown representation of the Annex IV documentation.

        The output includes all seven Annex IV sections with proper headings,
        JSON code blocks for structured metrics, and bullet-pointed limitations.

        Returns
        -------
        str
            A multi-section Markdown document.
        """
        sections: list[str] = [
            f"# Technical Documentation: {self.system_name}",
            "",
            "**Per EU AI Act (Regulation (EU) 2024/1689), Annex IV**",
            f"**Generated:** {self.generated_at}",
            f"**Provider:** {self.provider_name}",
            f"**System Version:** {self.system_version}",
            "",
            "---",
            "",
            "## 1. General Description of the AI System (Annex IV(1))",
            "",
            "### Intended Purpose",
            self.intended_purpose,
            "",
            "### System Description",
            self.system_description,
            "",
            "## 2. Development Process (Annex IV(2))",
            "",
            "### Design Specifications",
            self.design_specifications,
            "",
            "### Development Methodology",
            self.development_methodology,
            "",
            "### Validation Procedures",
            self.validation_procedures,
            "",
            "## 3. Monitoring, Functioning and Control (Annex IV(3))",
            "",
            "### Human Oversight Measures",
            self.human_oversight_measures,
            "",
            "### Shutdown / Override Procedures",
            self.shutdown_procedures,
            "",
            "## 4. Risk Management (Annex IV(4))",
            "",
            "### Risk Assessment",
            self.risk_assessment,
            "",
            "### Risk Mitigation",
            self.risk_mitigation_measures,
            "",
            "## 5. Data Governance (Annex IV(5))",
            "",
            "### Training Data Description",
            self.training_data_description,
            "",
            "### Data Preparation",
            self.data_preparation_methods,
            "",
            "### Data Quality Metrics",
            self.data_quality_metrics,
            "",
            "## 6. Performance and Testing (Annex IV(6))",
            "",
            "### Performance Metrics",
            "```json",
            json.dumps(self.performance_metrics, indent=2),
            "```",
            "",
            "### Testing Results",
            "```json",
            json.dumps(self.testing_results, indent=2),
            "```",
            "",
            "### Known Limitations",
        ]
        for limitation in self.known_limitations:
            sections.append(f"- {limitation}")
        sections.extend([
            "",
            "## 7. Cybersecurity Assessment (Annex IV(7))",
            "",
            "### Assessment",
            self.cybersecurity_assessment,
            "",
            "### Robustness Measures",
            self.robustness_measures,
            "",
            "### Security Scan Results",
            "```json",
            json.dumps(self.security_scan_results, indent=2),
            "```",
        ])
        return "\n".join(sections)

    def export(self, output_dir: str) -> list[str]:
        """Export the documentation package to files on disk.

        Creates the output directory if it does not exist, then writes:

        - ``annex-iv-technical-documentation.md`` — human-readable Markdown.
        - ``annex-iv-data.json`` — full dataclass serialised to JSON.

        Parameters
        ----------
        output_dir:
            Path to the directory where files should be written.

        Returns
        -------
        list[str]
            Absolute paths of all files created, in the order they were written.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        created: list[str] = []

        md_path = out_path / "annex-iv-technical-documentation.md"
        md_path.write_text(self.to_markdown(), encoding="utf-8")
        created.append(str(md_path))

        json_path = out_path / "annex-iv-data.json"
        json_path.write_text(
            json.dumps(dataclasses.asdict(self), indent=2),
            encoding="utf-8",
        )
        created.append(str(json_path))

        return created

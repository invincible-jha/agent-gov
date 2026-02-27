"""Tests for EU AI Act Annex IV technical documentation generator."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from agent_gov.frameworks.eu_ai_act_docs import AnnexIVDocumentation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_full_doc() -> AnnexIVDocumentation:
    """Return a fully-populated documentation instance for tests."""
    return AnnexIVDocumentation(
        system_name="TestSystem v1",
        system_version="1.0.0",
        provider_name="Acme AI GmbH",
        intended_purpose="Automated loan risk scoring.",
        system_description="ML model trained on credit bureau data.",
        design_specifications="Gradient-boosted decision tree.",
        development_methodology="Agile, iterative training pipeline.",
        validation_procedures="5-fold cross-validation, hold-out test set.",
        human_oversight_measures="Monthly model audits by risk team.",
        shutdown_procedures="Manual kill-switch in admin dashboard.",
        risk_assessment="Fairness audit completed Q1 2025.",
        risk_mitigation_measures="Bias correction applied during training.",
        training_data_description="3 years of anonymised loan applications.",
        data_preparation_methods="Normalisation, outlier removal.",
        data_quality_metrics="99.2% completeness, <0.1% duplicates.",
        performance_metrics={"auc": 0.92, "accuracy": 0.88},
        testing_results={"fairness_score": 0.95},
        known_limitations=["Not validated on non-EU data", "Requires annual re-training"],
        cybersecurity_assessment="Penetration test completed 2024-12.",
        robustness_measures="Adversarial training applied.",
        security_scan_results={"vulnerabilities_found": 0},
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestAnnexIVDocumentationConstruction:
    def test_default_construction_succeeds(self) -> None:
        doc = AnnexIVDocumentation()
        assert doc.system_name == ""
        assert doc.system_version == ""
        assert doc.provider_name == ""

    def test_default_performance_metrics_is_empty_dict(self) -> None:
        doc = AnnexIVDocumentation()
        assert doc.performance_metrics == {}

    def test_default_testing_results_is_empty_dict(self) -> None:
        doc = AnnexIVDocumentation()
        assert doc.testing_results == {}

    def test_default_known_limitations_is_empty_list(self) -> None:
        doc = AnnexIVDocumentation()
        assert doc.known_limitations == []

    def test_default_security_scan_results_is_empty_dict(self) -> None:
        doc = AnnexIVDocumentation()
        assert doc.security_scan_results == {}

    def test_generated_at_is_populated_by_default(self) -> None:
        doc = AnnexIVDocumentation()
        assert doc.generated_at != ""

    def test_eu_ai_act_version_is_set(self) -> None:
        doc = AnnexIVDocumentation()
        assert "2024/1689" in doc.eu_ai_act_version

    def test_is_dataclass(self) -> None:
        doc = AnnexIVDocumentation()
        assert dataclasses.is_dataclass(doc)

    def test_full_construction_preserves_values(self) -> None:
        doc = _make_full_doc()
        assert doc.system_name == "TestSystem v1"
        assert doc.provider_name == "Acme AI GmbH"
        assert doc.performance_metrics == {"auc": 0.92, "accuracy": 0.88}

    def test_mutable_defaults_are_independent(self) -> None:
        doc_a = AnnexIVDocumentation()
        doc_b = AnnexIVDocumentation()
        doc_a.known_limitations.append("limitation")
        assert "limitation" not in doc_b.known_limitations


# ---------------------------------------------------------------------------
# to_markdown()
# ---------------------------------------------------------------------------


class TestToMarkdown:
    def test_returns_string(self) -> None:
        doc = AnnexIVDocumentation(system_name="MySystem")
        assert isinstance(doc.to_markdown(), str)

    def test_contains_system_name_in_title(self) -> None:
        doc = AnnexIVDocumentation(system_name="CreditBot")
        md = doc.to_markdown()
        assert "CreditBot" in md

    def test_contains_all_seven_annex_iv_sections(self) -> None:
        doc = _make_full_doc()
        md = doc.to_markdown()
        assert "Annex IV(1)" in md
        assert "Annex IV(2)" in md
        assert "Annex IV(3)" in md
        assert "Annex IV(4)" in md
        assert "Annex IV(5)" in md
        assert "Annex IV(6)" in md
        assert "Annex IV(7)" in md

    def test_contains_provider_name(self) -> None:
        doc = AnnexIVDocumentation(provider_name="Acme Corp")
        md = doc.to_markdown()
        assert "Acme Corp" in md

    def test_contains_system_version(self) -> None:
        doc = AnnexIVDocumentation(system_version="3.2.1")
        md = doc.to_markdown()
        assert "3.2.1" in md

    def test_performance_metrics_as_json_block(self) -> None:
        doc = AnnexIVDocumentation(performance_metrics={"auc": 0.92})
        md = doc.to_markdown()
        assert "```json" in md
        assert '"auc"' in md

    def test_testing_results_as_json_block(self) -> None:
        doc = AnnexIVDocumentation(testing_results={"fairness": 0.95})
        md = doc.to_markdown()
        assert '"fairness"' in md

    def test_security_scan_results_as_json_block(self) -> None:
        doc = AnnexIVDocumentation(security_scan_results={"vulns": 0})
        md = doc.to_markdown()
        assert '"vulns"' in md

    def test_known_limitations_as_bullet_points(self) -> None:
        doc = AnnexIVDocumentation(
            known_limitations=["Limitation A", "Limitation B"]
        )
        md = doc.to_markdown()
        assert "- Limitation A" in md
        assert "- Limitation B" in md

    def test_empty_known_limitations_no_bullets(self) -> None:
        doc = AnnexIVDocumentation(known_limitations=[])
        md = doc.to_markdown()
        # Should not error; just no bullet lines for limitations section body.
        assert "Known Limitations" in md

    def test_regulation_reference_in_markdown(self) -> None:
        doc = AnnexIVDocumentation()
        md = doc.to_markdown()
        assert "2024/1689" in md

    def test_markdown_starts_with_h1(self) -> None:
        doc = AnnexIVDocumentation(system_name="MyBot")
        md = doc.to_markdown()
        assert md.startswith("# Technical Documentation: MyBot")


# ---------------------------------------------------------------------------
# export()
# ---------------------------------------------------------------------------


class TestExport:
    def test_export_creates_markdown_file(self, tmp_path: Path) -> None:
        doc = _make_full_doc()
        output_dir = str(tmp_path / "docs")
        created = doc.export(output_dir)
        md_files = [f for f in created if f.endswith(".md")]
        assert len(md_files) == 1
        assert Path(md_files[0]).exists()

    def test_export_creates_json_file(self, tmp_path: Path) -> None:
        doc = _make_full_doc()
        output_dir = str(tmp_path / "docs")
        created = doc.export(output_dir)
        json_files = [f for f in created if f.endswith(".json")]
        assert len(json_files) == 1
        assert Path(json_files[0]).exists()

    def test_export_returns_two_paths(self, tmp_path: Path) -> None:
        doc = AnnexIVDocumentation()
        created = doc.export(str(tmp_path / "out"))
        assert len(created) == 2

    def test_export_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "nested" / "deep" / "docs"
        assert not new_dir.exists()
        doc = AnnexIVDocumentation()
        doc.export(str(new_dir))
        assert new_dir.exists()

    def test_export_markdown_contains_system_name(self, tmp_path: Path) -> None:
        doc = AnnexIVDocumentation(system_name="ExportedSystem")
        created = doc.export(str(tmp_path))
        md_path = next(f for f in created if f.endswith(".md"))
        content = Path(md_path).read_text(encoding="utf-8")
        assert "ExportedSystem" in content

    def test_export_json_round_trips(self, tmp_path: Path) -> None:
        doc = _make_full_doc()
        created = doc.export(str(tmp_path))
        json_path = next(f for f in created if f.endswith(".json"))
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        assert data["system_name"] == "TestSystem v1"
        assert data["performance_metrics"] == {"auc": 0.92, "accuracy": 0.88}

    def test_export_json_matches_asdict(self, tmp_path: Path) -> None:
        doc = _make_full_doc()
        created = doc.export(str(tmp_path))
        json_path = next(f for f in created if f.endswith(".json"))
        from_file = json.loads(Path(json_path).read_text(encoding="utf-8"))
        from_asdict = dataclasses.asdict(doc)
        assert from_file == from_asdict

    def test_export_markdown_filename(self, tmp_path: Path) -> None:
        doc = AnnexIVDocumentation()
        created = doc.export(str(tmp_path))
        md_files = [Path(f).name for f in created if f.endswith(".md")]
        assert "annex-iv-technical-documentation.md" in md_files

    def test_export_json_filename(self, tmp_path: Path) -> None:
        doc = AnnexIVDocumentation()
        created = doc.export(str(tmp_path))
        json_files = [Path(f).name for f in created if f.endswith(".json")]
        assert "annex-iv-data.json" in json_files

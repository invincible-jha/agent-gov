"""Tests for the EU AI Act CLI commands: classify and document.

Uses Click's CliRunner for isolation — no filesystem side-effects outside
of pytest's tmp_path.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_gov.cli.main import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# classify command
# ---------------------------------------------------------------------------


class TestClassifyCommand:
    def test_classify_exits_zero_with_valid_description(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            cli, ["classify", "--description", "A spam email filter."]
        )
        assert result.exit_code == 0

    def test_classify_default_format_is_table(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli, ["classify", "--description", "A spam email filter."]
        )
        # Table output should not be raw JSON at the top level.
        assert result.exit_code == 0
        # Output contains a risk level label (not a JSON dict key).
        assert "MINIMAL" in result.output or "minimal" in result.output.lower()

    def test_classify_json_format_returns_valid_json(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "A customer service chatbot.",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "level" in data
        assert "obligations" in data
        assert "confidence" in data

    def test_classify_json_format_high_risk(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Automated recruitment and cv screening system.",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["level"] == "high"

    def test_classify_shows_risk_level_in_table_output(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            cli, ["classify", "--description", "A movie recommendation system."]
        )
        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert any(level in output_lower for level in ["minimal", "limited", "high", "unacceptable"])

    def test_classify_high_risk_shows_high_in_table(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Facial recognition system for biometric access.",
            ],
        )
        assert result.exit_code == 0
        assert "HIGH" in result.output or "high" in result.output.lower()

    def test_classify_unacceptable_risk_in_json(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Social scoring platform for public citizens.",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["level"] == "unacceptable"

    def test_classify_with_use_case_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Generic ML pipeline.",
                "--use-case", "cv screening",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["level"] == "high"

    def test_classify_with_multiple_use_cases(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Enterprise AI tool.",
                "--use-case", "hiring",
                "--use-case", "recruitment",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["level"] == "high"

    def test_classify_with_data_category_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Data processing tool.",
                "--data-category", "biometric",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["level"] == "high"

    def test_classify_missing_description_fails(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["classify"])
        assert result.exit_code != 0

    def test_classify_json_contains_article_references(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "Facial recognition biometric system.",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data["article_references"], list)

    def test_classify_json_confidence_is_float(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "classify",
                "--description", "A movie recommendation engine.",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data["confidence"], float)

    def test_classify_short_description_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli, ["classify", "-d", "spam filter", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "level" in data


# ---------------------------------------------------------------------------
# document command
# ---------------------------------------------------------------------------


class TestDocumentCommand:
    def test_document_exits_zero_with_required_options(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "TestBot",
                "--provider", "Acme GmbH",
                "--description", "Automated test system.",
                "--output", output_dir,
            ],
        )
        assert result.exit_code == 0

    def test_document_creates_markdown_file(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        runner.invoke(
            cli,
            [
                "document",
                "--system-name", "TestBot",
                "--provider", "Acme GmbH",
                "--description", "An AI assistant.",
                "--output", output_dir,
            ],
        )
        md_path = Path(output_dir) / "annex-iv-technical-documentation.md"
        assert md_path.exists()

    def test_document_creates_json_file_with_both_format(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        runner.invoke(
            cli,
            [
                "document",
                "--system-name", "TestBot",
                "--provider", "Acme GmbH",
                "--description", "An AI assistant.",
                "--output", output_dir,
                "--format", "both",
            ],
        )
        json_path = Path(output_dir) / "annex-iv-data.json"
        assert json_path.exists()

    def test_document_markdown_only_format(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "MdOnly",
                "--provider", "Provider",
                "--description", "Markdown only test.",
                "--output", output_dir,
                "--format", "markdown",
            ],
        )
        assert result.exit_code == 0
        assert (Path(output_dir) / "annex-iv-technical-documentation.md").exists()
        # JSON should NOT be created for markdown-only format.
        assert not (Path(output_dir) / "annex-iv-data.json").exists()

    def test_document_json_only_format(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "JsonOnly",
                "--provider", "Provider",
                "--description", "JSON only test.",
                "--output", output_dir,
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        assert (Path(output_dir) / "annex-iv-data.json").exists()
        assert not (Path(output_dir) / "annex-iv-technical-documentation.md").exists()

    def test_document_missing_system_name_fails(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        result = runner.invoke(
            cli,
            [
                "document",
                "--provider", "Acme GmbH",
                "--description", "Some system.",
                "--output", str(tmp_path),
            ],
        )
        assert result.exit_code != 0

    def test_document_missing_provider_fails(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "SomeBot",
                "--description", "Some system.",
                "--output", str(tmp_path),
            ],
        )
        assert result.exit_code != 0

    def test_document_missing_description_fails(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "SomeBot",
                "--provider", "Acme GmbH",
                "--output", str(tmp_path),
            ],
        )
        assert result.exit_code != 0

    def test_document_missing_output_fails(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "SomeBot",
                "--provider", "Acme GmbH",
                "--description", "Some system.",
            ],
        )
        assert result.exit_code != 0

    def test_document_output_mentions_system_name(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        result = runner.invoke(
            cli,
            [
                "document",
                "--system-name", "UniqueSystemName",
                "--provider", "Provider",
                "--description", "A system.",
                "--output", output_dir,
            ],
        )
        assert result.exit_code == 0
        assert "UniqueSystemName" in result.output

    def test_document_creates_output_directory(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        new_dir = tmp_path / "deeply" / "nested" / "output"
        assert not new_dir.exists()
        runner.invoke(
            cli,
            [
                "document",
                "--system-name", "DirTest",
                "--provider", "Provider",
                "--description", "Dir creation test.",
                "--output", str(new_dir),
            ],
        )
        assert new_dir.exists()

    def test_document_json_output_is_valid_json(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output_dir = str(tmp_path / "docs")
        runner.invoke(
            cli,
            [
                "document",
                "--system-name", "JsonTest",
                "--provider", "Provider",
                "--description", "JSON validation test.",
                "--output", output_dir,
                "--format", "json",
            ],
        )
        json_path = Path(output_dir) / "annex-iv-data.json"
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["system_name"] == "JsonTest"

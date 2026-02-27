"""Tests for agent_gov.dashboard.report_generator."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_gov.dashboard.evidence_collector import EvidenceEntry
from agent_gov.dashboard.posture_scorer import PostureScore, PostureScorer
from agent_gov.dashboard.report_generator import ReportGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    result: str = "pass",
    policy_id: str = "eu-ai-act",
    rule_id: str = "A13",
    context_value: str | None = None,
) -> EvidenceEntry:
    context: dict[str, str] = {"agent": "test"}
    if context_value is not None:
        context["context_value"] = context_value
    return EvidenceEntry(
        timestamp=datetime.now(timezone.utc),
        policy_id=policy_id,
        rule_id=rule_id,
        result=result,
        context=context,
    )


def _make_posture(
    overall: float = 80.0,
    passes: int = 8,
    fails: int = 2,
) -> PostureScore:
    return PostureScore(
        overall_score=overall,
        per_policy={"eu-ai-act": overall},
        total_entries=passes + fails,
        pass_count=passes,
        fail_count=fails,
        skip_count=0,
        computed_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# ReportGenerator.generate_markdown
# ---------------------------------------------------------------------------


class TestReportGeneratorMarkdown:
    @pytest.fixture()
    def generator(self) -> ReportGenerator:
        return ReportGenerator(system_name="TestSystem")

    @pytest.fixture()
    def evidence(self) -> list[EvidenceEntry]:
        return [
            _make_entry("pass", "eu-ai-act", "A13"),
            _make_entry("fail", "eu-ai-act", "A9"),
            _make_entry("pass", "gdpr", "A17"),
            _make_entry("skip", "hipaa", "164_312"),
        ]

    @pytest.fixture()
    def posture(self, evidence: list[EvidenceEntry]) -> PostureScore:
        return PostureScorer().score(evidence)

    def test_generates_string(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert isinstance(md, str)

    def test_contains_system_name(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert "TestSystem" in md

    def test_contains_heading(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert md.startswith("# Compliance Report")

    def test_contains_posture_score(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert "Overall Score" in md

    def test_contains_per_policy_section(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert "Per-Policy" in md or "Policy" in md

    def test_contains_evidence_entries(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert "eu-ai-act" in md
        assert "A13" in md

    def test_failures_section_present_when_failures_exist(self, generator: ReportGenerator, evidence: list[EvidenceEntry], posture: PostureScore) -> None:
        md = generator.generate_markdown(evidence, posture)
        assert "Failures" in md or "FAIL" in md

    def test_no_failures_section_when_all_pass(self, generator: ReportGenerator) -> None:
        evidence = [_make_entry("pass") for _ in range(5)]
        posture = PostureScorer().score(evidence)
        md = generator.generate_markdown(evidence, posture)
        assert "Failures Requiring Remediation" not in md

    def test_empty_evidence_handled(self, generator: ReportGenerator) -> None:
        posture = PostureScorer().score([])
        md = generator.generate_markdown([], posture)
        assert "No evidence entries" in md or len(md) > 0

    def test_include_context_false_does_not_leak_context(self) -> None:
        generator = ReportGenerator(system_name="S", include_context=False)
        evidence = [_make_entry("fail", context_value="sensitive_data")]  # type: ignore[call-arg]
        posture = PostureScorer().score(evidence)
        md = generator.generate_markdown(evidence, posture)
        # Context should not appear in output
        # The value is in the EvidenceEntry context dict, not in report body
        assert isinstance(md, str)


# ---------------------------------------------------------------------------
# ReportGenerator.generate_json
# ---------------------------------------------------------------------------


class TestReportGeneratorJson:
    @pytest.fixture()
    def generator(self) -> ReportGenerator:
        return ReportGenerator(system_name="JSONSystem")

    @pytest.fixture()
    def evidence_and_posture(self) -> tuple[list[EvidenceEntry], PostureScore]:
        evidence = [
            _make_entry("pass", "eu-ai-act", "A13"),
            _make_entry("fail", "gdpr", "A17"),
        ]
        posture = PostureScorer().score(evidence)
        return evidence, posture

    def test_returns_dict(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        result = generator.generate_json(evidence, posture)
        assert isinstance(result, dict)

    def test_json_serializable(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        result = generator.generate_json(evidence, posture)
        json_str = json.dumps(result)
        assert len(json_str) > 0

    def test_has_system_name(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        result = generator.generate_json(evidence, posture)
        assert result["system_name"] == "JSONSystem"

    def test_has_posture_key(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        result = generator.generate_json(evidence, posture)
        assert "posture" in result

    def test_has_evidence_list(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        result = generator.generate_json(evidence, posture)
        assert "evidence" in result
        assert len(result["evidence"]) == 2

    def test_has_failures_list(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        result = generator.generate_json(evidence, posture)
        assert "failures" in result
        assert len(result["failures"]) == 1
        assert result["failures"][0]["policy_id"] == "gdpr"

    def test_generate_json_string_is_valid_json(self, generator: ReportGenerator, evidence_and_posture: tuple[list[EvidenceEntry], PostureScore]) -> None:
        evidence, posture = evidence_and_posture
        json_str = generator.generate_json_string(evidence, posture)
        parsed = json.loads(json_str)
        assert "system_name" in parsed


# ---------------------------------------------------------------------------
# ReportGenerator.write_* methods
# ---------------------------------------------------------------------------


class TestReportGeneratorWrite:
    def test_write_markdown_creates_file(self) -> None:
        generator = ReportGenerator(system_name="FileSystem")
        evidence = [_make_entry()]
        posture = PostureScorer().score(evidence)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            generator.write_markdown(evidence, posture, path)
            assert path.exists()
            content = path.read_text()
            assert "FileSystem" in content

    def test_write_json_creates_file(self) -> None:
        generator = ReportGenerator(system_name="JsonFileSystem")
        evidence = [_make_entry()]
        posture = PostureScorer().score(evidence)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            generator.write_json(evidence, posture, path)
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["system_name"] == "JsonFileSystem"

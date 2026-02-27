"""Tests for agent_gov.reporting — generator, json_report, markdown, templates."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_gov.reporting.generator import ReportGenerator
from agent_gov.reporting.json_report import JsonReporter
from agent_gov.reporting.markdown import MarkdownReporter, _fallback_compliance, _fallback_governance
from agent_gov.reporting import templates as _templates_pkg


# ---------------------------------------------------------------------------
# JsonReporter
# ---------------------------------------------------------------------------


class TestJsonReporter:
    def test_render_returns_json_string(self) -> None:
        reporter = JsonReporter()
        result = reporter.render({"key": "value", "num": 42})
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_render_with_custom_indent(self) -> None:
        reporter = JsonReporter(indent=4)
        result = reporter.render({"a": 1})
        assert "    " in result  # 4-space indent

    def test_render_non_json_types_stringified(self) -> None:
        from datetime import datetime, timezone

        reporter = JsonReporter()
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = reporter.render({"ts": ts})
        assert "2024" in result

    def test_write_creates_file(self, tmp_path: Path) -> None:
        reporter = JsonReporter()
        output = tmp_path / "report.json"
        written = reporter.write({"hello": "world"}, output)
        assert written.exists()
        content = json.loads(written.read_text())
        assert content["hello"] == "world"

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        reporter = JsonReporter()
        output = tmp_path / "nested" / "deep" / "report.json"
        written = reporter.write({"x": 1}, output)
        assert written.exists()

    def test_write_returns_resolved_path(self, tmp_path: Path) -> None:
        reporter = JsonReporter()
        output = tmp_path / "out.json"
        returned = reporter.write({}, output)
        assert returned.is_absolute()


# ---------------------------------------------------------------------------
# MarkdownReporter
# ---------------------------------------------------------------------------


class TestMarkdownReporter:
    def _governance_payload(self) -> dict:
        return {
            "title": "Test Governance Report",
            "generated_at": "2024-01-01T00:00:00+00:00",
            "policy_name": "standard",
            "audit_summary": {
                "total_entries": 10,
                "pass_count": 8,
                "fail_count": 2,
                "agents": ["agent-1", "agent-2"],
                "action_types": ["search", "write"],
            },
            "evaluation_results": [],
            "pass_rate_percent": 80.0,
        }

    def _compliance_payload(self) -> dict:
        return {
            "title": "Compliance Report",
            "generated_at": "2024-01-01T00:00:00+00:00",
            "overall_score": 75.0,
            "framework_count": 1,
            "frameworks": [
                {
                    "framework": "gdpr",
                    "score_percent": 75.0,
                    "passed": 3,
                    "total": 4,
                    "results": [
                        {"id": "A1", "name": "Privacy", "status": "pass"},
                        {"id": "A2", "name": "Rights", "status": "fail"},
                    ],
                }
            ],
        }

    def test_render_governance_returns_string(self) -> None:
        reporter = MarkdownReporter()
        result = reporter.render_governance(self._governance_payload())
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_governance_contains_title(self) -> None:
        reporter = MarkdownReporter()
        result = reporter.render_governance(self._governance_payload())
        assert "Test Governance Report" in result

    def test_render_compliance_returns_string(self) -> None:
        reporter = MarkdownReporter()
        result = reporter.render_compliance(self._compliance_payload())
        assert isinstance(result, str)

    def test_write_governance_creates_file(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        output = tmp_path / "gov.md"
        written = reporter.write_governance(self._governance_payload(), output)
        assert written.exists()
        assert "Report" in written.read_text()

    def test_write_compliance_creates_file(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        output = tmp_path / "comp.md"
        written = reporter.write_compliance(self._compliance_payload(), output)
        assert written.exists()

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        output = tmp_path / "sub" / "dir" / "report.md"
        written = reporter.write_governance(self._governance_payload(), output)
        assert written.exists()


class TestFallbackGovernance:
    def test_contains_title(self) -> None:
        payload = {
            "title": "My Report",
            "generated_at": "2024",
            "policy_name": "pol",
            "pass_rate_percent": 90,
            "audit_summary": {"total_entries": 5, "pass_count": 4, "fail_count": 1, "agents": ["a"]},
            "evaluation_results": [
                {"passed": True, "policy_name": "pol", "violation_count": 0, "highest_severity": "none"}
            ],
        }
        result = _fallback_governance(payload)
        assert "My Report" in result
        assert "PASS" in result

    def test_no_evals_shows_message(self) -> None:
        payload = {
            "title": "Report",
            "generated_at": "now",
            "policy_name": None,
            "pass_rate_percent": None,
            "audit_summary": {},
            "evaluation_results": [],
        }
        result = _fallback_governance(payload)
        assert "No evaluation results" in result

    def test_non_dict_audit_summary_ignored(self) -> None:
        payload = {
            "title": "T",
            "generated_at": "now",
            "policy_name": None,
            "pass_rate_percent": None,
            "audit_summary": "bad",
            "evaluation_results": [],
        }
        result = _fallback_governance(payload)
        assert isinstance(result, str)


class TestFallbackCompliance:
    def test_contains_title(self) -> None:
        payload = {
            "title": "Compliance",
            "generated_at": "now",
            "overall_score": 50.0,
            "frameworks": [
                {
                    "framework": "hipaa",
                    "score_percent": 50.0,
                    "passed": 2,
                    "total": 4,
                    "results": [
                        {"id": "H1", "name": "Encryption", "status": "pass"},
                    ],
                }
            ],
        }
        result = _fallback_compliance(payload)
        assert "Compliance" in result
        assert "hipaa" in result

    def test_non_dict_framework_skipped(self) -> None:
        payload = {
            "title": "T",
            "generated_at": "now",
            "overall_score": 0.0,
            "frameworks": ["not-a-dict"],
        }
        result = _fallback_compliance(payload)
        assert isinstance(result, str)

    def test_status_icons(self) -> None:
        payload = {
            "title": "T",
            "generated_at": "now",
            "overall_score": 0.0,
            "frameworks": [
                {
                    "framework": "fw",
                    "score_percent": 0.0,
                    "passed": 0,
                    "total": 3,
                    "results": [
                        {"id": "A", "name": "A", "status": "pass"},
                        {"id": "B", "name": "B", "status": "fail"},
                        {"id": "C", "name": "C", "status": "unknown"},
                    ],
                }
            ],
        }
        result = _fallback_compliance(payload)
        assert "[x]" in result
        assert "[ ]" in result
        assert "[?]" in result


# ---------------------------------------------------------------------------
# ReportGenerator
# ---------------------------------------------------------------------------


class TestReportGenerator:
    def test_governance_report_no_reader_no_evals(self) -> None:
        gen = ReportGenerator()
        payload = gen.governance_report(title="My Governance Report")
        assert payload["title"] == "My Governance Report"
        assert payload["audit_summary"] == {}
        assert payload["pass_rate_percent"] is None

    def test_governance_report_with_policy_name(self) -> None:
        gen = ReportGenerator()
        payload = gen.governance_report(policy_name="standard")
        assert payload["policy_name"] == "standard"

    def test_governance_report_with_reader(self, tmp_path: Path) -> None:
        from agent_gov.audit.entry import AuditEntry
        from agent_gov.audit.reader import AuditReader
        from datetime import datetime, timezone

        log_file = tmp_path / "audit.jsonl"
        entries = [
            AuditEntry("a", "search", {}, "pass", "standard"),
            AuditEntry("b", "write", {}, "fail", "standard"),
        ]
        log_file.write_text("\n".join(e.to_json() for e in entries) + "\n")

        reader = AuditReader(log_file)
        gen = ReportGenerator(audit_reader=reader)
        payload = gen.governance_report(policy_name="standard")

        summary = payload["audit_summary"]
        assert isinstance(summary, dict)
        assert summary["total_entries"] == 2

    def test_governance_report_pass_rate_computed(self, tmp_path: Path) -> None:
        from agent_gov.audit.entry import AuditEntry
        from agent_gov.audit.reader import AuditReader

        log_file = tmp_path / "audit.jsonl"
        entries = [AuditEntry("a", "s", {}, "pass", "p"), AuditEntry("b", "s", {}, "pass", "p")]
        log_file.write_text("\n".join(e.to_json() for e in entries) + "\n")

        reader = AuditReader(log_file)
        gen = ReportGenerator(audit_reader=reader)
        payload = gen.governance_report()
        assert payload["pass_rate_percent"] == 100.0

    def test_governance_report_with_eval_reports(self, tmp_path: Path) -> None:
        from agent_gov.policy.evaluator import PolicyEvaluator
        from agent_gov.policy.loader import PolicyLoader

        policy_yaml = tmp_path / "p.yaml"
        policy_yaml.write_text(
            "name: test-pol\nversion: '1.0'\nrules:\n  - name: pii-rule\n    type: pii_check\n    enabled: true\n    severity: high\n"
        )
        loader = PolicyLoader()
        policy = loader.load_file(str(policy_yaml))
        evaluator = PolicyEvaluator()
        report = evaluator.evaluate(policy, {"type": "search"})

        gen = ReportGenerator()
        payload = gen.governance_report(evaluation_reports=[report])
        assert len(payload["evaluation_results"]) == 1  # type: ignore[arg-type]

    def test_compliance_report_empty_frameworks(self) -> None:
        gen = ReportGenerator()
        payload = gen.compliance_report(framework_reports=[])
        assert payload["overall_score"] == 0.0
        assert payload["framework_count"] == 0

    def test_compliance_report_with_frameworks(self) -> None:
        from agent_gov.frameworks.eu_ai_act import EuAiActFramework

        fw = EuAiActFramework()
        report = fw.run_check({"A6": {"status": "pass"}})

        gen = ReportGenerator()
        payload = gen.compliance_report(framework_reports=[report])
        assert payload["framework_count"] == 1
        assert isinstance(payload["overall_score"], float)

    def test_full_report_with_both(self, tmp_path: Path) -> None:
        from agent_gov.frameworks.gdpr import GdprFramework

        fw = GdprFramework()
        fw_report = fw.run_check({})

        gen = ReportGenerator()
        payload = gen.full_report(framework_reports=[fw_report])
        assert "governance" in payload
        assert "compliance" in payload

    def test_full_report_no_frameworks_compliance_empty(self) -> None:
        gen = ReportGenerator()
        payload = gen.full_report()
        assert payload["compliance"] == {}


# ---------------------------------------------------------------------------
# Templates package (agent_gov.reporting.templates package __init__)
# ---------------------------------------------------------------------------


class TestTemplatesPackage:
    """Tests for the agent_gov.reporting.templates package (directory with __init__.py)."""

    def test_list_templates_returns_j2_files(self) -> None:
        names = _templates_pkg.list_templates()
        assert isinstance(names, list)
        assert all(n.endswith(".j2") or n.endswith(".jinja2") for n in names)

    def test_list_templates_sorted(self) -> None:
        names = _templates_pkg.list_templates()
        assert names == sorted(names)

    def test_get_template_governance_returns_string(self) -> None:
        # Try to get governance template
        names = _templates_pkg.list_templates()
        if names:
            content = _templates_pkg.get_template(names[0])
            assert isinstance(content, str)

    def test_get_template_missing_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            _templates_pkg.get_template("nonexistent.j2")

    def test_write_template_copies_file(self, tmp_path: Path) -> None:
        names = _templates_pkg.list_templates()
        if not names:
            pytest.skip("No templates available")
        output = tmp_path / "copied.j2"
        returned = _templates_pkg.write_template(names[0], output)
        assert returned.exists()

    def test_write_template_creates_parent_dirs(self, tmp_path: Path) -> None:
        names = _templates_pkg.list_templates()
        if not names:
            pytest.skip("No templates available")
        output = tmp_path / "sub" / "dir" / "template.j2"
        _templates_pkg.write_template(names[0], output)
        assert output.exists()

    def test_write_template_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _templates_pkg.write_template("nope.j2", tmp_path / "out.j2")


# ---------------------------------------------------------------------------
# Standalone templates.py (TEMPLATES dict — loaded via importlib since the
# package directory shadows it in normal import resolution)
# ---------------------------------------------------------------------------


class TestTemplatesStandaloneModule:
    """Cover agent_gov/reporting/templates.py (the file, not the package)."""

    @pytest.fixture(autouse=True)
    def _load_module(self) -> None:
        import importlib.util, os

        src = (
            Path(__file__).parent.parent.parent
            / "src" / "agent_gov" / "reporting" / "templates.py"
        )
        spec = importlib.util.spec_from_file_location("_standalone_templates", src)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self._mod = mod

    def test_templates_dict_has_known_keys(self) -> None:
        assert "minimal" in self._mod.TEMPLATES
        assert "basic" in self._mod.TEMPLATES
        assert "full" in self._mod.TEMPLATES

    def test_list_templates_sorted(self) -> None:
        names = self._mod.list_templates()
        assert names == sorted(names)

    def test_get_template_returns_yaml_string(self) -> None:
        content = self._mod.get_template("minimal")
        assert isinstance(content, str)
        assert "name:" in content

    def test_get_template_unknown_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="Unknown template"):
            self._mod.get_template("nope")

    def test_write_template_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "out.yaml"
        returned = self._mod.write_template("basic", output)
        assert output.exists()
        assert "pii_check" in output.read_text()

    def test_write_template_creates_parent_dirs(self, tmp_path: Path) -> None:
        output = tmp_path / "sub" / "dir" / "policy.yaml"
        self._mod.write_template("full", output)
        assert output.exists()

    def test_write_template_unknown_raises(self, tmp_path: Path) -> None:
        with pytest.raises(KeyError):
            self._mod.write_template("nope", tmp_path / "out.yaml")

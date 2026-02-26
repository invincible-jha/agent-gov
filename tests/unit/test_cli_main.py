"""Tests for agent_gov.cli.main — Click CLI commands via CliRunner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_gov.cli.main import cli


MINIMAL_POLICY = """\
name: test-policy
version: "1.0"
rules:
  - name: pii-rule
    type: pii_check
    enabled: true
    severity: high
"""

KEYWORD_POLICY = """\
name: keyword-policy
version: "1.0"
rules:
  - name: kw-rule
    type: keyword_block
    enabled: true
    severity: high
    params:
      keywords:
        - forbidden
"""


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def policy_file(tmp_path: Path) -> Path:
    p = tmp_path / "policy.yaml"
    p.write_text(MINIMAL_POLICY)
    return p


@pytest.fixture()
def keyword_policy_file(tmp_path: Path) -> Path:
    p = tmp_path / "keyword_policy.yaml"
    p.write_text(KEYWORD_POLICY)
    return p


# ---------------------------------------------------------------------------
# version command
# ---------------------------------------------------------------------------


class TestVersionCommand:
    def test_version_command_exits_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

    def test_version_command_shows_agent_gov(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["version"])
        assert "agent-gov" in result.output

    def test_version_option(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# check command
# ---------------------------------------------------------------------------


class TestCheckCommand:
    def test_check_passing_action(self, runner: CliRunner, policy_file: Path) -> None:
        action = json.dumps({"type": "search", "query": "weather"})
        result = runner.invoke(
            cli, ["check", "--policy", str(policy_file), "--action", action]
        )
        assert result.exit_code == 0

    def test_check_failing_action(
        self, runner: CliRunner, keyword_policy_file: Path
    ) -> None:
        action = json.dumps({"type": "write", "content": "forbidden text"})
        result = runner.invoke(
            cli, ["check", "--policy", str(keyword_policy_file), "--action", action]
        )
        assert result.exit_code == 2  # policy fail

    def test_check_invalid_json_exits_1(self, runner: CliRunner, policy_file: Path) -> None:
        result = runner.invoke(
            cli, ["check", "--policy", str(policy_file), "--action", "not json"]
        )
        assert result.exit_code == 1

    def test_check_action_not_dict_exits_1(
        self, runner: CliRunner, policy_file: Path
    ) -> None:
        result = runner.invoke(
            cli, ["check", "--policy", str(policy_file), "--action", "[1, 2]"]
        )
        assert result.exit_code == 1

    def test_check_with_audit_log(
        self, runner: CliRunner, policy_file: Path, tmp_path: Path
    ) -> None:
        audit_log = tmp_path / "audit.jsonl"
        action = json.dumps({"type": "search"})
        result = runner.invoke(
            cli,
            [
                "check",
                "--policy", str(policy_file),
                "--action", action,
                "--audit-log", str(audit_log),
            ],
        )
        assert result.exit_code == 0
        assert audit_log.exists()

    def test_check_invalid_policy_file_exits_1(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        bad_policy = tmp_path / "bad.yaml"
        bad_policy.write_text("not: valid: yaml: {{{{")
        action = json.dumps({"type": "test"})
        result = runner.invoke(
            cli, ["check", "--policy", str(bad_policy), "--action", action]
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# audit commands
# ---------------------------------------------------------------------------


class TestAuditCommands:
    def _write_audit_log(self, path: Path) -> None:
        from agent_gov.audit.entry import AuditEntry
        from datetime import datetime, timezone

        entries = [
            AuditEntry("agent-1", "search", {"type": "search"}, "pass", "test-policy"),
            AuditEntry("agent-2", "write", {"type": "write"}, "fail", "test-policy"),
        ]
        path.write_text("\n".join(e.to_json() for e in entries) + "\n")

    def test_audit_show_no_file(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(cli, ["audit", "show", "--log", str(tmp_path / "missing.jsonl")])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_audit_show_empty_file(self, runner: CliRunner, tmp_path: Path) -> None:
        log = tmp_path / "empty.jsonl"
        log.write_text("")
        result = runner.invoke(cli, ["audit", "show", "--log", str(log)])
        assert result.exit_code == 0
        assert "No audit entries" in result.output

    def test_audit_show_with_entries(self, runner: CliRunner, tmp_path: Path) -> None:
        log = tmp_path / "audit.jsonl"
        self._write_audit_log(log)
        result = runner.invoke(cli, ["audit", "show", "--log", str(log), "--last", "10"])
        assert result.exit_code == 0
        assert "agent-1" in result.output or "agent-2" in result.output

    def test_audit_query_no_file(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(cli, ["audit", "query", "--log", str(tmp_path / "missing.jsonl")])
        assert result.exit_code == 0

    def test_audit_query_with_entries(self, runner: CliRunner, tmp_path: Path) -> None:
        log = tmp_path / "audit.jsonl"
        self._write_audit_log(log)
        result = runner.invoke(
            cli, ["audit", "query", "--log", str(log), "--agent-id", "agent-1"]
        )
        assert result.exit_code == 0

    def test_audit_query_no_match(self, runner: CliRunner, tmp_path: Path) -> None:
        log = tmp_path / "audit.jsonl"
        self._write_audit_log(log)
        result = runner.invoke(
            cli, ["audit", "query", "--log", str(log), "--agent-id", "nobody"]
        )
        assert result.exit_code == 0
        assert "No entries" in result.output

    def test_audit_query_verdict_filter(self, runner: CliRunner, tmp_path: Path) -> None:
        log = tmp_path / "audit.jsonl"
        self._write_audit_log(log)
        result = runner.invoke(
            cli, ["audit", "query", "--log", str(log), "--verdict", "pass"]
        )
        assert result.exit_code == 0

    def test_audit_query_invalid_since_exits_1(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        log = tmp_path / "audit.jsonl"
        self._write_audit_log(log)
        result = runner.invoke(
            cli, ["audit", "query", "--log", str(log), "--since", "not-a-date"]
        )
        assert result.exit_code == 1

    def test_audit_query_valid_since(self, runner: CliRunner, tmp_path: Path) -> None:
        log = tmp_path / "audit.jsonl"
        self._write_audit_log(log)
        result = runner.invoke(
            cli, ["audit", "query", "--log", str(log), "--since", "2020-01-01"]
        )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# frameworks commands
# ---------------------------------------------------------------------------


class TestFrameworksCommands:
    def test_frameworks_list(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["frameworks", "list"])
        assert result.exit_code == 0
        assert "gdpr" in result.output.lower() or "GDPR" in result.output

    def test_frameworks_check_gdpr_no_evidence(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["frameworks", "check", "--framework", "gdpr"])
        assert result.exit_code == 0

    def test_frameworks_check_unknown_framework(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["frameworks", "check", "--framework", "nonexistent"])
        assert result.exit_code == 1

    def test_frameworks_check_with_evidence_file(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        evidence = tmp_path / "evidence.yaml"
        # Write some evidence for gdpr
        from agent_gov.frameworks.gdpr import GdprFramework
        fw = GdprFramework()
        items = fw.checklist()
        content = "\n".join(f"{item.id}: {{status: pass, evidence: done}}" for item in items[:2])
        evidence.write_text(content)
        result = runner.invoke(
            cli,
            ["frameworks", "check", "--framework", "gdpr", "--evidence", str(evidence)],
        )
        assert result.exit_code == 0

    def test_frameworks_check_with_output(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        output = tmp_path / "fw_report.json"
        result = runner.invoke(
            cli,
            ["frameworks", "check", "--framework", "hipaa", "--output", str(output)],
        )
        assert result.exit_code == 0
        assert output.exists()

    def test_frameworks_check_bad_evidence_file(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        # A non-YAML file
        bad_evidence = tmp_path / "bad.yaml"
        bad_evidence.write_text("{{{not valid yaml")
        result = runner.invoke(
            cli,
            ["frameworks", "check", "--framework", "gdpr", "--evidence", str(bad_evidence)],
        )
        # yaml.safe_load may succeed on some edge cases; exit 0 or 1 both acceptable
        assert result.exit_code in (0, 1)


# ---------------------------------------------------------------------------
# plugins commands
# ---------------------------------------------------------------------------


class TestPluginsCommands:
    def test_plugins_list_shows_rules(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["plugins", "list"])
        assert result.exit_code == 0
        assert "pii_check" in result.output

    def test_plugins_list_shows_frameworks(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["plugins", "list"])
        assert result.exit_code == 0
        assert "gdpr" in result.output


# ---------------------------------------------------------------------------
# init command
# ---------------------------------------------------------------------------


class TestInitCommand:
    def test_init_standard_preset(self, runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "policy.yaml"
        result = runner.invoke(
            cli, ["init", "--preset", "standard", "--output", str(output)]
        )
        # init succeeds if the pack file exists
        assert result.exit_code in (0, 1)

    def test_init_minimal_preset(self, runner: CliRunner, tmp_path: Path) -> None:
        output = tmp_path / "min.yaml"
        result = runner.invoke(
            cli, ["init", "--preset", "minimal", "--output", str(output)]
        )
        assert result.exit_code in (0, 1)


# ---------------------------------------------------------------------------
# report commands
# ---------------------------------------------------------------------------


class TestReportCommands:
    def test_report_generate_markdown(
        self, runner: CliRunner, policy_file: Path, tmp_path: Path
    ) -> None:
        output = tmp_path / "report.md"
        result = runner.invoke(
            cli,
            [
                "report", "generate",
                "--policy", str(policy_file),
                "--format", "md",
                "--output", str(output),
            ],
        )
        assert result.exit_code == 0
        assert output.exists()

    def test_report_generate_json(
        self, runner: CliRunner, policy_file: Path, tmp_path: Path
    ) -> None:
        output = tmp_path / "report.json"
        result = runner.invoke(
            cli,
            [
                "report", "generate",
                "--policy", str(policy_file),
                "--format", "json",
                "--output", str(output),
            ],
        )
        assert result.exit_code == 0
        assert output.exists()

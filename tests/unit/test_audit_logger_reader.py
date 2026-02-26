"""Tests for agent_gov.audit.logger and agent_gov.audit.reader."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from agent_gov.audit.entry import AuditEntry
from agent_gov.audit.logger import AuditLogger, _apply_filters
from agent_gov.audit.reader import AuditReader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(
    agent_id: str = "agent-1",
    action_type: str = "search",
    verdict: str = "pass",
    policy_name: str = "standard",
    timestamp: datetime | None = None,
) -> AuditEntry:
    if timestamp is None:
        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return AuditEntry(
        agent_id=agent_id,
        action_type=action_type,
        action_data={"type": action_type},
        verdict=verdict,
        policy_name=policy_name,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# AuditLogger
# ---------------------------------------------------------------------------


class TestAuditLogger:
    def test_log_creates_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        logger.log(_entry())
        assert log_file.exists()

    def test_log_appends_entries(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        logger.log(_entry(agent_id="a1"))
        logger.log(_entry(agent_id="a2"))
        lines = log_file.read_text().splitlines()
        assert len(lines) == 2

    def test_log_path_property(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        assert logger.log_path == log_file

    def test_log_creates_parent_dirs(self, tmp_path: Path) -> None:
        log_file = tmp_path / "nested" / "deep" / "audit.jsonl"
        logger = AuditLogger(log_file)
        logger.log(_entry())
        assert log_file.exists()

    def test_read_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        logger = AuditLogger(tmp_path / "missing.jsonl")
        assert logger.read() == []

    def test_read_skips_corrupted_lines(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        log_file.write_text('not-json\n{"agent_id":"x","action_type":"y","action_data":{},"verdict":"pass","policy_name":"p"}\n')
        logger = AuditLogger(log_file)
        entries = logger.read()
        assert len(entries) == 1

    def test_read_skips_blank_lines(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        e = _entry()
        log_file.write_text(e.to_json() + "\n\n")
        logger = AuditLogger(log_file)
        assert len(logger.read()) == 1

    def test_count_returns_correct_number(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        for _ in range(5):
            logger.log(_entry())
        assert logger.count() == 5

    def test_count_zero_for_missing_file(self, tmp_path: Path) -> None:
        logger = AuditLogger(tmp_path / "missing.jsonl")
        assert logger.count() == 0

    def test_query_filters_by_agent_id(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        logger.log(_entry(agent_id="alice"))
        logger.log(_entry(agent_id="bob"))
        result = logger.query({"agent_id": "alice"})
        assert all(e.agent_id == "alice" for e in result)
        assert len(result) == 1

    def test_query_filters_by_verdict(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        logger.log(_entry(verdict="pass"))
        logger.log(_entry(verdict="fail"))
        result = logger.query({"verdict": "fail"})
        assert len(result) == 1
        assert result[0].verdict == "fail"

    def test_log_from_report_writes_entry(self, tmp_path: Path) -> None:
        from agent_gov.policy.evaluator import PolicyEvaluator
        from agent_gov.policy.loader import PolicyLoader

        loader = PolicyLoader()
        policy_yaml = tmp_path / "p.yaml"
        policy_yaml.write_text(
            "name: test-policy\nversion: '1.0'\nrules:\n  - name: pii-rule\n    type: pii_check\n    enabled: true\n    severity: high\n"
        )
        policy = loader.load_file(str(policy_yaml))
        evaluator = PolicyEvaluator()
        report = evaluator.evaluate(policy, {"type": "search", "query": "hello"})

        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        entry = logger.log_from_report(report, agent_id="test-agent")

        assert entry.agent_id == "test-agent"
        assert entry.policy_name == "test-policy"
        assert log_file.exists()

    def test_log_from_report_wrong_type_raises(self, tmp_path: Path) -> None:
        logger = AuditLogger(tmp_path / "a.jsonl")
        with pytest.raises(TypeError, match="EvaluationReport"):
            logger.log_from_report({"not": "a report"}, agent_id="x")  # type: ignore[arg-type]

    def test_log_from_report_with_metadata(self, tmp_path: Path) -> None:
        from agent_gov.policy.evaluator import PolicyEvaluator
        from agent_gov.policy.loader import PolicyLoader

        loader = PolicyLoader()
        policy_yaml = tmp_path / "p.yaml"
        policy_yaml.write_text(
            "name: test-policy\nversion: '1.0'\nrules:\n  - name: pii-rule\n    type: pii_check\n    enabled: true\n    severity: high\n"
        )
        policy = loader.load_file(str(policy_yaml))
        evaluator = PolicyEvaluator()
        report = evaluator.evaluate(policy, {"type": "search"})

        log_file = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_file)
        entry = logger.log_from_report(report, agent_id="x", metadata={"run": "1"})
        assert entry.metadata == {"run": "1"}


# ---------------------------------------------------------------------------
# _apply_filters
# ---------------------------------------------------------------------------


class TestApplyFilters:
    def _entries(self) -> list[AuditEntry]:
        base_ts = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        return [
            _entry("alice", "search", "pass", "pol-a", base_ts),
            _entry("bob", "delete", "fail", "pol-b", base_ts + timedelta(hours=1)),
            _entry("alice", "write", "fail", "pol-a", base_ts + timedelta(hours=2)),
        ]

    def test_filter_by_action_type(self) -> None:
        result = _apply_filters(self._entries(), {"action_type": "delete"})
        assert len(result) == 1
        assert result[0].action_type == "delete"

    def test_filter_by_policy_name(self) -> None:
        result = _apply_filters(self._entries(), {"policy_name": "pol-a"})
        assert len(result) == 2

    def test_filter_by_since(self) -> None:
        cutoff = datetime(2024, 6, 1, 1, 30, 0, tzinfo=timezone.utc)
        result = _apply_filters(self._entries(), {"since": cutoff})
        assert len(result) == 1

    def test_filter_by_until(self) -> None:
        cutoff = datetime(2024, 6, 1, 0, 30, 0, tzinfo=timezone.utc)
        result = _apply_filters(self._entries(), {"until": cutoff})
        assert len(result) == 1

    def test_empty_filters_returns_all(self) -> None:
        entries = self._entries()
        result = _apply_filters(entries, {})
        assert result == entries

    def test_unknown_keys_ignored(self) -> None:
        entries = self._entries()
        result = _apply_filters(entries, {"unknown_key": "whatever"})
        assert result == entries

    def test_since_not_datetime_is_ignored(self) -> None:
        entries = self._entries()
        result = _apply_filters(entries, {"since": "2024-01-01"})
        assert result == entries

    def test_until_not_datetime_is_ignored(self) -> None:
        entries = self._entries()
        result = _apply_filters(entries, {"until": "2024-12-31"})
        assert result == entries


# ---------------------------------------------------------------------------
# AuditReader
# ---------------------------------------------------------------------------


class TestAuditReader:
    def _write_entries(self, path: Path, *entries: AuditEntry) -> None:
        path.write_text("\n".join(e.to_json() for e in entries) + "\n")

    def test_all_returns_all_entries(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entries = [_entry("a"), _entry("b"), _entry("c")]
        self._write_entries(log_file, *entries)
        reader = AuditReader(log_file)
        assert len(reader.all()) == 3

    def test_log_path_property(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        reader = AuditReader(log_file)
        assert reader.log_path == log_file

    def test_last_returns_most_recent(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entries = [_entry(agent_id=f"agent-{i}") for i in range(10)]
        self._write_entries(log_file, *entries)
        reader = AuditReader(log_file)
        last = reader.last(3)
        assert len(last) == 3
        assert last[-1].agent_id == "agent-9"

    def test_last_zero_returns_empty(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(log_file, _entry())
        reader = AuditReader(log_file)
        assert reader.last(0) == []

    def test_last_more_than_total_returns_all(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(log_file, _entry(), _entry())
        reader = AuditReader(log_file)
        assert len(reader.last(100)) == 2

    def test_query_by_agent_id(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(log_file, _entry("alice"), _entry("bob"), _entry("alice"))
        reader = AuditReader(log_file)
        result = reader.query(agent_id="alice")
        assert len(result) == 2

    def test_query_by_verdict(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(
            log_file, _entry(verdict="pass"), _entry(verdict="fail"), _entry(verdict="fail")
        )
        reader = AuditReader(log_file)
        assert len(reader.query(verdict="fail")) == 2

    def test_query_by_action_type(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(log_file, _entry(action_type="search"), _entry(action_type="delete"))
        reader = AuditReader(log_file)
        assert len(reader.query(action_type="search")) == 1

    def test_query_by_policy_name(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(
            log_file, _entry(policy_name="pol-a"), _entry(policy_name="pol-b")
        )
        reader = AuditReader(log_file)
        assert len(reader.query(policy_name="pol-a")) == 1

    def test_query_by_since(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self._write_entries(
            log_file,
            _entry(timestamp=base),
            _entry(timestamp=base + timedelta(hours=2)),
        )
        reader = AuditReader(log_file)
        result = reader.query(since=base + timedelta(hours=1))
        assert len(result) == 1

    def test_query_by_until(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self._write_entries(
            log_file,
            _entry(timestamp=base),
            _entry(timestamp=base + timedelta(hours=2)),
        )
        reader = AuditReader(log_file)
        result = reader.query(until=base + timedelta(hours=1))
        assert len(result) == 1

    def test_query_no_filters_returns_all(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        self._write_entries(log_file, _entry(), _entry(), _entry())
        reader = AuditReader(log_file)
        assert len(reader.query()) == 3

    def test_stats_empty_log(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        log_file.write_text("")
        reader = AuditReader(log_file)
        stats = reader.stats()
        assert stats["total"] == 0
        assert stats["pass_count"] == 0
        assert stats["fail_count"] == 0
        assert stats["earliest"] is None
        assert stats["latest"] is None

    def test_stats_with_entries(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self._write_entries(
            log_file,
            _entry("alice", "search", "pass", "pol-a", base),
            _entry("bob", "delete", "fail", "pol-b", base + timedelta(hours=5)),
        )
        reader = AuditReader(log_file)
        stats = reader.stats()
        assert stats["total"] == 2
        assert stats["pass_count"] == 1
        assert stats["fail_count"] == 1
        assert "alice" in stats["agents"]
        assert "bob" in stats["agents"]
        assert stats["earliest"] is not None
        assert stats["latest"] is not None

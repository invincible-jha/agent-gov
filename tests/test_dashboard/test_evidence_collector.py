"""Tests for agent_gov.dashboard.evidence_collector."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_gov.dashboard.evidence_collector import EvidenceCollector, EvidenceEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    policy_id: str = "eu-ai-act",
    rule_id: str = "A13",
    result: str = "pass",
    **context_kwargs: object,
) -> EvidenceEntry:
    """Build a test evidence entry."""
    return EvidenceEntry(
        timestamp=datetime.now(timezone.utc),
        policy_id=policy_id,
        rule_id=rule_id,
        result=result,
        context=dict(context_kwargs),
    )


# ---------------------------------------------------------------------------
# EvidenceEntry unit tests
# ---------------------------------------------------------------------------


class TestEvidenceEntry:
    def test_frozen_dataclass(self) -> None:
        entry = _make_entry()
        with pytest.raises((AttributeError, TypeError)):
            entry.policy_id = "changed"  # type: ignore[misc]

    def test_to_dict_has_required_keys(self) -> None:
        entry = _make_entry(policy_id="gdpr", rule_id="A17")
        d = entry.to_dict()
        assert "timestamp" in d
        assert "policy_id" in d
        assert "rule_id" in d
        assert "result" in d
        assert "context" in d

    def test_to_dict_values(self) -> None:
        entry = _make_entry(policy_id="hipaa", rule_id="164_312", result="fail")
        d = entry.to_dict()
        assert d["policy_id"] == "hipaa"
        assert d["rule_id"] == "164_312"
        assert d["result"] == "fail"

    def test_to_dict_timestamp_is_iso_string(self) -> None:
        entry = _make_entry()
        d = entry.to_dict()
        # Should not raise
        datetime.fromisoformat(d["timestamp"])

    def test_from_dict_round_trip(self) -> None:
        original = _make_entry(policy_id="eu-ai-act", rule_id="A6", agent="test-agent")
        reconstructed = EvidenceEntry.from_dict(original.to_dict())
        assert reconstructed.policy_id == original.policy_id
        assert reconstructed.rule_id == original.rule_id
        assert reconstructed.result == original.result
        assert reconstructed.context == original.context

    def test_from_dict_missing_timestamp_uses_now(self) -> None:
        data = {"policy_id": "x", "rule_id": "y", "result": "pass", "context": {}}
        entry = EvidenceEntry.from_dict(data)
        assert entry.timestamp.tzinfo is not None

    def test_from_dict_malformed_timestamp_uses_now(self) -> None:
        data = {
            "timestamp": "not-a-date",
            "policy_id": "x",
            "rule_id": "y",
            "result": "pass",
            "context": {},
        }
        entry = EvidenceEntry.from_dict(data)
        assert entry.timestamp.tzinfo is not None

    def test_context_preserved(self) -> None:
        entry = _make_entry(foo="bar", count=42)
        assert entry.context["foo"] == "bar"
        assert entry.context["count"] == 42


# ---------------------------------------------------------------------------
# EvidenceCollector.record and basic read
# ---------------------------------------------------------------------------


class TestEvidenceCollectorRecord:
    def test_record_increases_count(self) -> None:
        collector = EvidenceCollector()
        assert collector.count == 0
        collector.record(_make_entry())
        assert collector.count == 1

    def test_record_many_increases_count(self) -> None:
        collector = EvidenceCollector()
        collector.record_many([_make_entry(), _make_entry(), _make_entry()])
        assert collector.count == 3

    def test_all_entries_returns_all(self) -> None:
        collector = EvidenceCollector()
        entries = [_make_entry(rule_id=str(i)) for i in range(5)]
        collector.record_many(entries)
        assert len(collector.all_entries()) == 5

    def test_all_entries_preserves_order(self) -> None:
        collector = EvidenceCollector()
        rule_ids = ["A6", "A9", "A13"]
        for rid in rule_ids:
            collector.record(_make_entry(rule_id=rid))
        stored = [e.rule_id for e in collector.all_entries()]
        assert stored == rule_ids

    def test_max_entries_evicts_oldest(self) -> None:
        collector = EvidenceCollector(max_entries=3)
        for i in range(5):
            collector.record(_make_entry(rule_id=str(i)))
        entries = collector.all_entries()
        assert len(entries) == 3
        assert entries[0].rule_id == "2"  # oldest evicted: 0, 1

    def test_clear_removes_all(self) -> None:
        collector = EvidenceCollector()
        collector.record_many([_make_entry() for _ in range(10)])
        collector.clear()
        assert collector.count == 0


# ---------------------------------------------------------------------------
# EvidenceCollector.query
# ---------------------------------------------------------------------------


class TestEvidenceCollectorQuery:
    @pytest.fixture()
    def populated_collector(self) -> EvidenceCollector:
        collector = EvidenceCollector()
        collector.record(_make_entry(policy_id="eu-ai-act", rule_id="A13", result="pass"))
        collector.record(_make_entry(policy_id="eu-ai-act", rule_id="A9", result="fail"))
        collector.record(_make_entry(policy_id="gdpr", rule_id="A17", result="pass"))
        collector.record(_make_entry(policy_id="gdpr", rule_id="A35", result="skip"))
        collector.record(_make_entry(policy_id="hipaa", rule_id="164_312", result="pass"))
        return collector

    def test_query_no_filters_returns_all(self, populated_collector: EvidenceCollector) -> None:
        assert len(populated_collector.query()) == 5

    def test_query_by_policy_id(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(policy_id="eu-ai-act")
        assert len(results) == 2
        assert all(e.policy_id == "eu-ai-act" for e in results)

    def test_query_by_rule_id(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(rule_id="A13")
        assert len(results) == 1
        assert results[0].rule_id == "A13"

    def test_query_by_result_pass(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(result="pass")
        assert len(results) == 3

    def test_query_by_result_fail(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(result="fail")
        assert len(results) == 1
        assert results[0].rule_id == "A9"

    def test_query_by_result_skip(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(result="skip")
        assert len(results) == 1

    def test_query_combined_filters(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(policy_id="gdpr", result="pass")
        assert len(results) == 1
        assert results[0].rule_id == "A17"

    def test_query_nonexistent_policy_returns_empty(self, populated_collector: EvidenceCollector) -> None:
        results = populated_collector.query(policy_id="soc2")
        assert results == []

    def test_query_since_filter(self) -> None:
        collector = EvidenceCollector()
        ts_early = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ts_late = datetime(2025, 6, 1, tzinfo=timezone.utc)
        collector.record(EvidenceEntry(timestamp=ts_early, policy_id="p", rule_id="r", result="pass", context={}))
        collector.record(EvidenceEntry(timestamp=ts_late, policy_id="p", rule_id="r2", result="pass", context={}))
        results = collector.query(since=datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert len(results) == 1
        assert results[0].rule_id == "r2"

    def test_query_until_filter(self) -> None:
        collector = EvidenceCollector()
        ts_early = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ts_late = datetime(2025, 6, 1, tzinfo=timezone.utc)
        collector.record(EvidenceEntry(timestamp=ts_early, policy_id="p", rule_id="r", result="pass", context={}))
        collector.record(EvidenceEntry(timestamp=ts_late, policy_id="p", rule_id="r2", result="pass", context={}))
        results = collector.query(until=datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert len(results) == 1
        assert results[0].rule_id == "r"


# ---------------------------------------------------------------------------
# EvidenceCollector.policy_ids / rule_ids
# ---------------------------------------------------------------------------


class TestEvidenceCollectorMetadata:
    def test_policy_ids_empty_collector(self) -> None:
        collector = EvidenceCollector()
        assert collector.policy_ids() == []

    def test_policy_ids_deduplicated_and_sorted(self) -> None:
        collector = EvidenceCollector()
        collector.record(_make_entry(policy_id="gdpr"))
        collector.record(_make_entry(policy_id="eu-ai-act"))
        collector.record(_make_entry(policy_id="gdpr"))
        ids = collector.policy_ids()
        assert ids == sorted(set(ids))
        assert "gdpr" in ids
        assert "eu-ai-act" in ids
        assert len(ids) == 2

    def test_rule_ids_filtered_by_policy(self) -> None:
        collector = EvidenceCollector()
        collector.record(_make_entry(policy_id="eu-ai-act", rule_id="A13"))
        collector.record(_make_entry(policy_id="eu-ai-act", rule_id="A9"))
        collector.record(_make_entry(policy_id="gdpr", rule_id="A17"))
        ids = collector.rule_ids(policy_id="eu-ai-act")
        assert set(ids) == {"A13", "A9"}


# ---------------------------------------------------------------------------
# Export / import round-trip
# ---------------------------------------------------------------------------


class TestEvidenceCollectorExport:
    def test_export_json_creates_file(self) -> None:
        collector = EvidenceCollector()
        collector.record(_make_entry())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.jsonl"
            collector.export_json(path)
            assert path.exists()

    def test_export_json_is_valid_jsonl(self) -> None:
        collector = EvidenceCollector()
        collector.record(_make_entry(policy_id="eu-ai-act"))
        collector.record(_make_entry(policy_id="gdpr"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.jsonl"
            collector.export_json(path)
            lines = path.read_text().strip().splitlines()
            assert len(lines) == 2
            for line in lines:
                obj = json.loads(line)
                assert "policy_id" in obj

    def test_load_json_round_trip(self) -> None:
        collector = EvidenceCollector()
        collector.record(_make_entry(policy_id="eu-ai-act", rule_id="A13"))
        collector.record(_make_entry(policy_id="gdpr", rule_id="A17", result="fail"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.jsonl"
            collector.export_json(path)
            loaded = EvidenceCollector.load_json(path)
            assert loaded.count == 2
            assert loaded.query(policy_id="eu-ai-act")[0].rule_id == "A13"
            assert loaded.query(result="fail")[0].policy_id == "gdpr"

    def test_export_dict_structure(self) -> None:
        collector = EvidenceCollector()
        collector.record(_make_entry())
        data = collector.export_dict()
        assert "count" in data
        assert "entries" in data
        assert data["count"] == 1
        assert isinstance(data["entries"], list)

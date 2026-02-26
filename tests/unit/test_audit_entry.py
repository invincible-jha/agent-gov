"""Tests for agent_gov.audit.entry — AuditEntry serialisation and deserialisation."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from agent_gov.audit.entry import AuditEntry


def _make_entry(**kwargs) -> AuditEntry:
    defaults = dict(
        agent_id="agent-1",
        action_type="search",
        action_data={"query": "test"},
        verdict="pass",
        policy_name="standard",
    )
    defaults.update(kwargs)
    return AuditEntry(**defaults)


class TestAuditEntryToJson:
    def test_round_trip(self) -> None:
        entry = _make_entry()
        restored = AuditEntry.from_json(entry.to_json())
        assert restored.agent_id == entry.agent_id
        assert restored.action_type == entry.action_type
        assert restored.verdict == entry.verdict
        assert restored.policy_name == entry.policy_name

    def test_to_json_is_single_line(self) -> None:
        entry = _make_entry()
        json_str = entry.to_json()
        assert "\n" not in json_str

    def test_timestamp_serialised_as_iso(self) -> None:
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        entry = _make_entry(timestamp=ts)
        data = json.loads(entry.to_json())
        assert "2024-06-01" in data["timestamp"]

    def test_metadata_included(self) -> None:
        entry = _make_entry(metadata={"env": "prod"})
        data = json.loads(entry.to_json())
        assert data["metadata"] == {"env": "prod"}


class TestAuditEntryFromJson:
    def test_from_json_valid(self) -> None:
        raw = json.dumps({
            "agent_id": "bot",
            "action_type": "delete",
            "action_data": {"target": "file.txt"},
            "verdict": "fail",
            "policy_name": "strict",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "metadata": {},
        })
        entry = AuditEntry.from_json(raw)
        assert entry.agent_id == "bot"
        assert entry.verdict == "fail"
        assert entry.timestamp.tzinfo is not None

    def test_from_json_missing_required_fields_raises(self) -> None:
        raw = json.dumps({"agent_id": "x"})
        with pytest.raises(ValueError, match="missing required fields"):
            AuditEntry.from_json(raw)

    def test_from_json_malformed_raises(self) -> None:
        with pytest.raises(ValueError, match="Malformed JSON"):
            AuditEntry.from_json("not-json{{{")

    def test_from_json_not_dict_raises(self) -> None:
        with pytest.raises(ValueError, match="must be a JSON object"):
            AuditEntry.from_json("[1, 2, 3]")

    def test_from_json_bad_timestamp_defaults_to_now(self) -> None:
        raw = json.dumps({
            "agent_id": "x",
            "action_type": "y",
            "action_data": {},
            "verdict": "pass",
            "policy_name": "p",
            "timestamp": "not-a-date",
        })
        entry = AuditEntry.from_json(raw)
        assert entry.timestamp.tzinfo is not None

    def test_from_json_non_dict_action_data_defaults_to_empty(self) -> None:
        raw = json.dumps({
            "agent_id": "x",
            "action_type": "y",
            "action_data": "not-a-dict",
            "verdict": "pass",
            "policy_name": "p",
        })
        entry = AuditEntry.from_json(raw)
        assert entry.action_data == {}

    def test_from_json_non_dict_metadata_defaults_to_empty(self) -> None:
        raw = json.dumps({
            "agent_id": "x",
            "action_type": "y",
            "action_data": {},
            "verdict": "pass",
            "policy_name": "p",
            "metadata": "bad",
        })
        entry = AuditEntry.from_json(raw)
        assert entry.metadata == {}

    def test_from_json_timezone_naive_timestamp_gets_utc(self) -> None:
        raw = json.dumps({
            "agent_id": "x",
            "action_type": "y",
            "action_data": {},
            "verdict": "pass",
            "policy_name": "p",
            "timestamp": "2024-03-15T08:00:00",
        })
        entry = AuditEntry.from_json(raw)
        assert entry.timestamp.tzinfo == timezone.utc


class TestAuditEntryRepr:
    def test_repr_contains_agent_id(self) -> None:
        entry = _make_entry(agent_id="my-bot")
        assert "my-bot" in repr(entry)

    def test_repr_contains_verdict(self) -> None:
        entry = _make_entry(verdict="fail")
        assert "fail" in repr(entry)

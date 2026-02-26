"""Tests for agent_gov.audit.search — build_filter, search_entries, aggregations."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from agent_gov.audit.entry import AuditEntry
from agent_gov.audit.search import (
    aggregate_by_action_type,
    aggregate_by_agent,
    aggregate_by_policy,
    aggregate_verdicts,
    build_filter,
    search_entries,
)


def _entry(
    agent_id: str = "agent-1",
    action_type: str = "search",
    verdict: str = "pass",
    policy_name: str = "standard",
    timestamp: datetime | None = None,
) -> AuditEntry:
    if timestamp is None:
        timestamp = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    return AuditEntry(
        agent_id=agent_id,
        action_type=action_type,
        action_data={},
        verdict=verdict,
        policy_name=policy_name,
        timestamp=timestamp,
    )


BASE_TS = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

ENTRIES = [
    _entry("alice", "search", "pass", "pol-a", BASE_TS),
    _entry("bob", "delete", "fail", "pol-b", BASE_TS + timedelta(hours=1)),
    _entry("alice", "write", "fail", "pol-a", BASE_TS + timedelta(hours=2)),
    _entry("carol", "search", "pass", "pol-b", BASE_TS + timedelta(hours=3)),
]


class TestBuildFilter:
    def test_no_criteria_passes_all(self) -> None:
        fn = build_filter()
        assert all(fn(e) for e in ENTRIES)

    def test_agent_id_filter(self) -> None:
        fn = build_filter(agent_id="alice")
        matches = [e for e in ENTRIES if fn(e)]
        assert all(e.agent_id == "alice" for e in matches)
        assert len(matches) == 2

    def test_action_type_filter(self) -> None:
        fn = build_filter(action_type="search")
        matches = [e for e in ENTRIES if fn(e)]
        assert len(matches) == 2

    def test_verdict_filter(self) -> None:
        fn = build_filter(verdict="fail")
        matches = [e for e in ENTRIES if fn(e)]
        assert len(matches) == 2
        assert all(e.verdict == "fail" for e in matches)

    def test_policy_name_filter(self) -> None:
        fn = build_filter(policy_name="pol-b")
        matches = [e for e in ENTRIES if fn(e)]
        assert len(matches) == 2

    def test_since_filter(self) -> None:
        fn = build_filter(since=BASE_TS + timedelta(minutes=90))
        matches = [e for e in ENTRIES if fn(e)]
        assert len(matches) == 2

    def test_until_filter(self) -> None:
        fn = build_filter(until=BASE_TS + timedelta(minutes=30))
        matches = [e for e in ENTRIES if fn(e)]
        assert len(matches) == 1

    def test_combined_filters(self) -> None:
        fn = build_filter(agent_id="alice", verdict="fail")
        matches = [e for e in ENTRIES if fn(e)]
        assert len(matches) == 1
        assert matches[0].action_type == "write"

    def test_no_match_returns_empty(self) -> None:
        fn = build_filter(agent_id="nobody")
        assert [e for e in ENTRIES if fn(e)] == []


class TestSearchEntries:
    def test_returns_matching_entries(self) -> None:
        fn = build_filter(verdict="pass")
        result = search_entries(ENTRIES, fn)
        assert len(result) == 2

    def test_limit_caps_results(self) -> None:
        fn = build_filter()
        result = search_entries(ENTRIES, fn, limit=2)
        assert len(result) == 2

    def test_limit_one_returns_one(self) -> None:
        fn = build_filter()
        result = search_entries(ENTRIES, fn, limit=1)
        assert len(result) == 1

    def test_empty_list_returns_empty(self) -> None:
        fn = build_filter()
        assert search_entries([], fn) == []

    def test_preserves_order(self) -> None:
        fn = build_filter(agent_id="alice")
        result = search_entries(ENTRIES, fn)
        assert result[0].action_type == "search"
        assert result[1].action_type == "write"


class TestAggregateVerdicts:
    def test_counts_verdicts(self) -> None:
        counts = aggregate_verdicts(ENTRIES)
        assert counts["pass"] == 2
        assert counts["fail"] == 2

    def test_empty_returns_empty(self) -> None:
        assert aggregate_verdicts([]) == {}

    def test_only_pass_verdicts(self) -> None:
        entries = [_entry(verdict="pass") for _ in range(3)]
        counts = aggregate_verdicts(entries)
        assert counts == {"pass": 3}


class TestAggregateByAgent:
    def test_groups_by_agent(self) -> None:
        groups = aggregate_by_agent(ENTRIES)
        assert "alice" in groups
        assert "bob" in groups
        assert "carol" in groups
        assert len(groups["alice"]) == 2

    def test_empty_returns_empty_dict(self) -> None:
        assert aggregate_by_agent([]) == {}


class TestAggregateByActionType:
    def test_groups_by_action_type(self) -> None:
        groups = aggregate_by_action_type(ENTRIES)
        assert "search" in groups
        assert len(groups["search"]) == 2

    def test_empty_returns_empty_dict(self) -> None:
        assert aggregate_by_action_type([]) == {}


class TestAggregateByPolicy:
    def test_groups_by_policy(self) -> None:
        groups = aggregate_by_policy(ENTRIES)
        assert "pol-a" in groups
        assert len(groups["pol-a"]) == 2

    def test_empty_returns_empty_dict(self) -> None:
        assert aggregate_by_policy([]) == {}

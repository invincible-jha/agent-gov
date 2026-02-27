"""Tests for TraceReplayer."""
from __future__ import annotations

import json

import pytest

from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity
from agent_gov.simulation.trace_replayer import (
    AgentTrace,
    TraceEvent,
    TraceReplayer,
    TraceReplayResult,
)


def _make_permissive_policy() -> PolicyConfig:
    """Policy with no rules — everything passes."""
    return PolicyConfig(name="permissive", rules=[])


def _make_blocking_policy() -> PolicyConfig:
    """Policy that blocks any action containing PII keywords."""
    return PolicyConfig(
        name="block-pii",
        rules=[
            RuleConfig(
                name="block-pii",
                type="pii_check",
                severity=Severity.HIGH,
                params={"check_email": True},
            )
        ],
    )


def _make_simple_trace(num_events: int = 3, trace_id: str = "trace-1") -> AgentTrace:
    """Build a simple trace with non-PII events."""
    events = [
        TraceEvent(
            event_id=f"event-{i}",
            action={"type": "search", "query": f"safe query {i}"},
        )
        for i in range(num_events)
    ]
    return AgentTrace(trace_id=trace_id, agent_id="agent-1", events=events)


class TestTraceEvent:
    def test_frozen_is_hashable(self) -> None:
        event = TraceEvent(event_id="e1", action={"type": "read"})
        assert event in {event}

    def test_to_dict_structure(self) -> None:
        event = TraceEvent(
            event_id="e1",
            action={"type": "search"},
            timestamp="2024-01-01T00:00:00Z",
        )
        d = event.to_dict()
        assert d["event_id"] == "e1"
        assert d["action"] == {"type": "search"}
        assert d["timestamp"] == "2024-01-01T00:00:00Z"


class TestAgentTrace:
    def test_event_count(self) -> None:
        trace = _make_simple_trace(5)
        assert trace.event_count == 5

    def test_to_dict_structure(self) -> None:
        trace = _make_simple_trace(2, "trace-abc")
        d = trace.to_dict()
        assert d["trace_id"] == "trace-abc"
        assert d["event_count"] == 2
        assert len(d["events"]) == 2


class TestTraceReplayer:
    def setup_method(self) -> None:
        self.replayer = TraceReplayer()
        self.evaluator = PolicyEvaluator(strict=False)

    def test_load_dict_basic(self) -> None:
        data = {
            "trace_id": "t1",
            "agent_id": "agent-a",
            "events": [
                {"event_id": "e1", "action": {"type": "search"}},
            ],
        }
        trace = self.replayer.load_dict(data)
        assert trace.trace_id == "t1"
        assert trace.agent_id == "agent-a"
        assert trace.event_count == 1

    def test_load_dict_auto_generates_ids(self) -> None:
        data = {"events": [{"action": {"type": "read"}}]}
        trace = self.replayer.load_dict(data)
        assert trace.trace_id != ""
        assert trace.events[0].event_id == "event-0"

    def test_load_dict_rejects_non_dict(self) -> None:
        with pytest.raises(ValueError, match="dictionary"):
            self.replayer.load_dict([])  # type: ignore[arg-type]

    def test_load_dict_rejects_bad_events_type(self) -> None:
        with pytest.raises(ValueError, match="list"):
            self.replayer.load_dict({"events": "not-a-list"})

    def test_load_dict_rejects_non_dict_event(self) -> None:
        with pytest.raises(ValueError, match="dictionary"):
            self.replayer.load_dict({"events": ["bad"]})

    def test_load_json_valid(self) -> None:
        json_text = json.dumps({
            "trace_id": "t2",
            "agent_id": "agent-b",
            "events": [{"event_id": "e1", "action": {"type": "write", "content": "hello"}}],
        })
        trace = self.replayer.load_json(json_text)
        assert trace.trace_id == "t2"

    def test_load_json_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            self.replayer.load_json("{not valid json}")

    def test_replay_permissive_policy_all_pass(self) -> None:
        policy = _make_permissive_policy()
        trace = _make_simple_trace(3)
        result = self.replayer.replay(trace, policy, self.evaluator)
        assert isinstance(result, TraceReplayResult)
        assert result.total_events == 3
        assert result.passed_events == 3
        assert result.blocked_events == 0

    def test_replay_block_rate(self) -> None:
        policy = _make_permissive_policy()
        trace = _make_simple_trace(4)
        result = self.replayer.replay(trace, policy, self.evaluator)
        assert result.block_rate == 0.0

    def test_replay_empty_trace(self) -> None:
        policy = _make_permissive_policy()
        trace = AgentTrace(trace_id="empty", agent_id="agent-0", events=[])
        result = self.replayer.replay(trace, policy, self.evaluator)
        assert result.total_events == 0
        assert result.block_rate == 0.0

    def test_replay_event_results_keyed_by_event_id(self) -> None:
        policy = _make_permissive_policy()
        trace = _make_simple_trace(2, "t-check")
        result = self.replayer.replay(trace, policy, self.evaluator)
        assert "event-0" in result.event_results
        assert "event-1" in result.event_results

    def test_replay_to_dict_structure(self) -> None:
        policy = _make_permissive_policy()
        trace = _make_simple_trace(2)
        result = self.replayer.replay(trace, policy, self.evaluator)
        d = result.to_dict()
        assert "trace_id" in d
        assert "block_rate" in d
        assert "event_results" in d

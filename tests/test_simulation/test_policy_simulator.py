"""Tests for PolicySimulator."""
from __future__ import annotations

import pytest

from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity
from agent_gov.simulation.policy_simulator import (
    PolicySimulator,
    SimulationConfig,
    SimulationReport,
    TraceSimulationResult,
)
from agent_gov.simulation.trace_replayer import AgentTrace, TraceEvent


def _make_permissive_policy(name: str = "permissive") -> PolicyConfig:
    return PolicyConfig(name=name, rules=[])


def _make_pii_policy(name: str = "pii-blocker") -> PolicyConfig:
    return PolicyConfig(
        name=name,
        rules=[
            RuleConfig(
                name="block-pii",
                type="pii_check",
                severity=Severity.HIGH,
                params={"check_email": True},
            )
        ],
    )


def _make_trace(trace_id: str, actions: list[dict]) -> AgentTrace:
    events = [
        TraceEvent(event_id=f"{trace_id}-e{i}", action=action)
        for i, action in enumerate(actions)
    ]
    return AgentTrace(trace_id=trace_id, agent_id="test-agent", events=events)


class TestSimulationConfig:
    def test_basic_construction(self) -> None:
        policy = _make_permissive_policy()
        config = SimulationConfig(proposed_policy=policy)
        assert config.proposed_policy.name == "permissive"
        assert config.baseline_policy is None
        assert config.traces == []


class TestTraceSimulationResult:
    def test_to_dict_with_no_baseline(self) -> None:
        from agent_gov.simulation.trace_replayer import TraceReplayResult

        proposed = TraceReplayResult(
            trace_id="t1", total_events=5, blocked_events=2, passed_events=3
        )
        result = TraceSimulationResult(
            trace_id="t1", proposed_result=proposed, new_blocks=2
        )
        d = result.to_dict()
        assert d["trace_id"] == "t1"
        assert d["proposed_blocked"] == 2
        assert d["baseline_blocked"] == 0


class TestPolicySimulator:
    def setup_method(self) -> None:
        self.simulator = PolicySimulator()

    def test_simulate_no_traces_returns_empty_report(self) -> None:
        config = SimulationConfig(proposed_policy=_make_permissive_policy())
        report = self.simulator.simulate(config)
        assert isinstance(report, SimulationReport)
        assert report.total_events == 0
        assert report.would_block_count == 0
        assert report.impact_score == 0.0

    def test_simulate_permissive_policy_blocks_nothing(self) -> None:
        trace = _make_trace("t1", [
            {"type": "search", "query": "safe"},
            {"type": "read", "path": "/docs"},
        ])
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy(),
            traces=[trace],
        )
        report = self.simulator.simulate(config)
        assert report.would_block_count == 0
        assert report.false_positive_rate == 0.0
        assert report.block_rate == 0.0

    def test_simulate_with_baseline_computes_false_positive_rate(self) -> None:
        trace = _make_trace("t1", [
            {"type": "search", "query": "safe query 1"},
            {"type": "search", "query": "safe query 2"},
            {"type": "search", "query": "safe query 3"},
        ])
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy("new-policy"),
            baseline_policy=_make_permissive_policy("old-policy"),
            traces=[trace],
        )
        report = self.simulator.simulate(config)
        # Both policies pass everything → no false positives
        assert report.false_positive_rate == 0.0
        assert report.impact_score == 0.0

    def test_simulate_multiple_traces(self) -> None:
        traces = [
            _make_trace(f"trace-{i}", [{"type": "search", "query": f"q{i}"}])
            for i in range(3)
        ]
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy(),
            traces=traces,
        )
        report = self.simulator.simulate(config)
        assert report.total_events == 3
        assert len(report.trace_results) == 3

    def test_simulate_label_propagated(self) -> None:
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy(),
            label="my-simulation",
        )
        report = self.simulator.simulate(config)
        assert report.label == "my-simulation"

    def test_simulate_policy_names_in_report(self) -> None:
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy("proposed-v2"),
            baseline_policy=_make_permissive_policy("baseline-v1"),
        )
        report = self.simulator.simulate(config)
        assert report.proposed_policy_name == "proposed-v2"
        assert report.baseline_policy_name == "baseline-v1"

    def test_simulate_no_baseline_shows_none(self) -> None:
        config = SimulationConfig(proposed_policy=_make_permissive_policy())
        report = self.simulator.simulate(config)
        assert report.baseline_policy_name == "(none)"

    def test_simulate_to_dict_structure(self) -> None:
        config = SimulationConfig(proposed_policy=_make_permissive_policy())
        report = self.simulator.simulate(config)
        d = report.to_dict()
        assert "proposed_policy" in d
        assert "baseline_policy" in d
        assert "total_events" in d
        assert "would_block_count" in d
        assert "false_positive_rate" in d
        assert "impact_score" in d
        assert "trace_results" in d

    def test_simulate_net_new_blocks(self) -> None:
        config = SimulationConfig(proposed_policy=_make_permissive_policy())
        report = self.simulator.simulate(config)
        assert report.net_new_blocks == 0

    def test_simulate_trace_results_have_correct_trace_id(self) -> None:
        trace = _make_trace("my-trace", [{"type": "read"}])
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy(),
            traces=[trace],
        )
        report = self.simulator.simulate(config)
        assert report.trace_results[0].trace_id == "my-trace"

    def test_simulate_impact_score_in_range(self) -> None:
        trace = _make_trace("t", [{"type": "search"}])
        config = SimulationConfig(
            proposed_policy=_make_permissive_policy(),
            traces=[trace],
        )
        report = self.simulator.simulate(config)
        assert 0.0 <= report.impact_score <= 1.0

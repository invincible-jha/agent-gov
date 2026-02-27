"""TraceReplayer — load and replay JSON agent traces through a policy evaluator.

A trace is a JSON file containing a list of agent events. Each event represents
a single agent action that can be evaluated against a policy.

Example
-------
::

    from agent_gov.simulation.trace_replayer import TraceReplayer

    replayer = TraceReplayer()
    trace = replayer.load_json('{"events": [{"type": "search", "query": "test"}]}')
    results = replayer.replay(trace, policy, evaluator)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class TraceEvent:
    """A single event within an agent trace.

    Attributes
    ----------
    event_id:
        Unique identifier for this event within the trace.
    action:
        The action dictionary to be evaluated against a policy.
    timestamp:
        Optional ISO timestamp when this event occurred.
    metadata:
        Arbitrary additional metadata attached to the event.
    """

    event_id: str
    action: dict[str, object]
    timestamp: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Hash based on event_id only (action and metadata dicts are unhashable)."""
        return hash(self.event_id)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "event_id": self.event_id,
            "action": self.action,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class AgentTrace:
    """A collection of events from an agent execution session.

    Attributes
    ----------
    trace_id:
        Unique identifier for this trace session.
    agent_id:
        Identifier of the agent that generated this trace.
    events:
        Ordered list of events in the trace.
    source:
        Origin label (e.g. filename or system name) for this trace.
    """

    trace_id: str
    agent_id: str
    events: list[TraceEvent] = field(default_factory=list)
    source: str = ""

    @property
    def event_count(self) -> int:
        """Number of events in the trace."""
        return len(self.events)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "source": self.source,
            "event_count": self.event_count,
            "events": [e.to_dict() for e in self.events],
        }


@dataclass
class TraceReplayResult:
    """Result of replaying a single trace through a policy evaluator.

    Attributes
    ----------
    trace_id:
        ID of the replayed trace.
    total_events:
        Total number of events replayed.
    blocked_events:
        Number of events that were blocked by the policy.
    passed_events:
        Number of events that passed the policy.
    event_results:
        Per-event dictionary mapping event_id to pass/fail result.
    """

    trace_id: str
    total_events: int
    blocked_events: int
    passed_events: int
    event_results: dict[str, bool] = field(default_factory=dict)

    @property
    def block_rate(self) -> float:
        """Fraction of events that were blocked (0.0–1.0)."""
        if self.total_events == 0:
            return 0.0
        return self.blocked_events / self.total_events

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "trace_id": self.trace_id,
            "total_events": self.total_events,
            "blocked_events": self.blocked_events,
            "passed_events": self.passed_events,
            "block_rate": self.block_rate,
            "event_results": self.event_results,
        }


class TraceReplayer:
    """Load and replay agent execution traces through a policy evaluator.

    Traces can be loaded from JSON strings or plain dictionaries.

    Expected JSON format::

        {
            "trace_id": "optional-id",
            "agent_id": "agent-name",
            "events": [
                {"event_id": "1", "action": {"type": "search", "query": "test"}},
                {"event_id": "2", "action": {"type": "write", "content": "hello"}}
            ]
        }

    If ``trace_id`` or ``event_id`` fields are absent they are auto-generated.
    """

    def load_dict(self, data: dict[str, object], *, source: str = "") -> AgentTrace:
        """Build an AgentTrace from a plain dictionary.

        Parameters
        ----------
        data:
            Dictionary containing trace data.
        source:
            Optional label identifying where this trace came from.

        Returns
        -------
        AgentTrace
            Parsed trace object.

        Raises
        ------
        ValueError
            If the data is missing required fields or is malformed.
        """
        if not isinstance(data, dict):
            raise ValueError("Trace data must be a dictionary.")

        raw_events = data.get("events", [])
        if not isinstance(raw_events, list):
            raise ValueError("Trace 'events' field must be a list.")

        trace_id = str(data.get("trace_id", f"trace-{datetime.now(timezone.utc).timestamp()}"))
        agent_id = str(data.get("agent_id", "unknown-agent"))

        events: list[TraceEvent] = []
        for index, event_data in enumerate(raw_events):
            if not isinstance(event_data, dict):
                raise ValueError(f"Event at index {index} must be a dictionary.")
            action = event_data.get("action", {})
            if not isinstance(action, dict):
                raise ValueError(f"Event at index {index} must have an 'action' dictionary.")
            event_id = str(event_data.get("event_id", f"event-{index}"))
            timestamp = str(event_data.get("timestamp", ""))
            metadata = {
                k: v for k, v in event_data.items()
                if k not in ("event_id", "action", "timestamp")
            }
            events.append(
                TraceEvent(
                    event_id=event_id,
                    action=action,
                    timestamp=timestamp,
                    metadata=metadata,
                )
            )

        return AgentTrace(
            trace_id=trace_id,
            agent_id=agent_id,
            events=events,
            source=source,
        )

    def load_json(self, json_text: str, *, source: str = "") -> AgentTrace:
        """Parse a JSON string into an AgentTrace.

        Parameters
        ----------
        json_text:
            JSON string conforming to the trace format.
        source:
            Optional label identifying where this trace came from.

        Raises
        ------
        ValueError
            If the JSON is invalid or the structure is malformed.
        """
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON trace: {exc}") from exc
        return self.load_dict(data, source=source)

    def replay(
        self,
        trace: AgentTrace,
        policy: object,
        evaluator: object,
    ) -> TraceReplayResult:
        """Replay all events in a trace through the given policy evaluator.

        Parameters
        ----------
        trace:
            The agent trace to replay.
        policy:
            A PolicyConfig instance to evaluate events against.
        evaluator:
            A PolicyEvaluator instance with an ``evaluate(policy, action)`` method.

        Returns
        -------
        TraceReplayResult
            Counts of blocked and passed events with per-event results.
        """
        blocked = 0
        passed = 0
        event_results: dict[str, bool] = {}

        for event in trace.events:
            report = evaluator.evaluate(policy, event.action)
            event_passed = bool(report.passed)
            event_results[event.event_id] = event_passed
            if event_passed:
                passed += 1
            else:
                blocked += 1

        return TraceReplayResult(
            trace_id=trace.trace_id,
            total_events=trace.event_count,
            blocked_events=blocked,
            passed_events=passed,
            event_results=event_results,
        )

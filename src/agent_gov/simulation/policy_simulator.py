"""PolicySimulator — replay historical agent traces against proposed policy changes.

Compares the effect of a proposed policy against a baseline policy (or no policy)
by replaying a set of captured traces. Reports would_block count, false_positive_rate,
and an overall impact_score.

Example
-------
::

    from agent_gov.simulation.policy_simulator import PolicySimulator, SimulationConfig

    simulator = PolicySimulator()
    config = SimulationConfig(
        proposed_policy=new_policy,
        baseline_policy=old_policy,
        traces=[trace1, trace2],
    )
    report = simulator.simulate(config)
    print(report.would_block_count, report.false_positive_rate, report.impact_score)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig
from agent_gov.simulation.trace_replayer import AgentTrace, TraceReplayer, TraceReplayResult


@dataclass
class SimulationConfig:
    """Configuration for a policy simulation run.

    Attributes
    ----------
    proposed_policy:
        The new policy to evaluate against historical traces.
    baseline_policy:
        The existing policy to compare against.  When None, the baseline
        is treated as blocking nothing (all events pass).
    traces:
        List of historical agent traces to replay.
    label:
        Optional human-readable label for this simulation run.
    """

    proposed_policy: PolicyConfig
    baseline_policy: Optional[PolicyConfig] = None
    traces: list[AgentTrace] = field(default_factory=list)
    label: str = ""


@dataclass
class TraceSimulationResult:
    """Result for a single trace in the simulation.

    Attributes
    ----------
    trace_id:
        Identifier of the replayed trace.
    proposed_result:
        Replay result under the proposed policy.
    baseline_result:
        Replay result under the baseline policy (or None if no baseline).
    new_blocks:
        Number of events blocked by proposed but not by baseline.
    new_passes:
        Number of events passing proposed but blocked by baseline.
    """

    trace_id: str
    proposed_result: TraceReplayResult
    baseline_result: Optional[TraceReplayResult] = None
    new_blocks: int = 0
    new_passes: int = 0

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "trace_id": self.trace_id,
            "proposed_blocked": self.proposed_result.blocked_events,
            "proposed_passed": self.proposed_result.passed_events,
            "baseline_blocked": (
                self.baseline_result.blocked_events if self.baseline_result else 0
            ),
            "baseline_passed": (
                self.baseline_result.passed_events if self.baseline_result else None
            ),
            "new_blocks": self.new_blocks,
            "new_passes": self.new_passes,
        }


@dataclass
class SimulationReport:
    """Full simulation report comparing a proposed policy against a baseline.

    Attributes
    ----------
    label:
        Human-readable label from the SimulationConfig.
    proposed_policy_name:
        Name of the proposed policy.
    baseline_policy_name:
        Name of the baseline policy, or ``"(none)"`` if no baseline.
    trace_results:
        Per-trace simulation results.
    total_events:
        Total number of events across all traces.
    would_block_count:
        Total events that would be blocked by the proposed policy.
    baseline_block_count:
        Total events blocked by the baseline policy.
    false_positive_rate:
        Fraction of events newly blocked by proposed but not baseline.
        Represents potential over-blocking. Range 0.0–1.0.
    impact_score:
        Normalized measure of how much more restrictive the proposed policy
        is compared to the baseline. Range 0.0–1.0.
    """

    label: str
    proposed_policy_name: str
    baseline_policy_name: str
    trace_results: list[TraceSimulationResult] = field(default_factory=list)
    total_events: int = 0
    would_block_count: int = 0
    baseline_block_count: int = 0
    false_positive_rate: float = 0.0
    impact_score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "label": self.label,
            "proposed_policy": self.proposed_policy_name,
            "baseline_policy": self.baseline_policy_name,
            "total_events": self.total_events,
            "would_block_count": self.would_block_count,
            "baseline_block_count": self.baseline_block_count,
            "false_positive_rate": self.false_positive_rate,
            "impact_score": self.impact_score,
            "trace_results": [r.to_dict() for r in self.trace_results],
        }

    @property
    def net_new_blocks(self) -> int:
        """Events blocked by proposed but not baseline."""
        return self.would_block_count - self.baseline_block_count

    @property
    def block_rate(self) -> float:
        """Fraction of total events blocked by the proposed policy."""
        if self.total_events == 0:
            return 0.0
        return self.would_block_count / self.total_events


class PolicySimulator:
    """Simulate the effect of a proposed policy against historical agent traces.

    Replays all events from each trace against both the proposed and baseline
    policies using PolicyEvaluator. Computes aggregate statistics to help
    operators understand the impact of a policy change before deploying it.

    Parameters
    ----------
    evaluator:
        Optional PolicyEvaluator instance.  A fresh instance with default
        rules is created if not provided.

    Example
    -------
    ::

        simulator = PolicySimulator()
        report = simulator.simulate(config)
    """

    def __init__(self, *, evaluator: Optional[PolicyEvaluator] = None) -> None:
        self._evaluator = evaluator or PolicyEvaluator(strict=False)
        self._replayer = TraceReplayer()

    def simulate(self, config: SimulationConfig) -> SimulationReport:
        """Run the simulation for a given configuration.

        Parameters
        ----------
        config:
            Simulation configuration with proposed policy, optional baseline,
            and list of traces to replay.

        Returns
        -------
        SimulationReport
            Aggregated statistics comparing proposed vs. baseline policy impact.
        """
        trace_results: list[TraceSimulationResult] = []
        total_events = 0
        would_block_count = 0
        baseline_block_count = 0
        new_blocks_total = 0

        for trace in config.traces:
            # Replay under proposed policy
            proposed_result = self._replayer.replay(
                trace, config.proposed_policy, self._evaluator
            )

            # Replay under baseline policy (if provided)
            baseline_result: Optional[TraceReplayResult] = None
            if config.baseline_policy is not None:
                baseline_result = self._replayer.replay(
                    trace, config.baseline_policy, self._evaluator
                )

            # Calculate new blocks (events blocked by proposed but not baseline)
            new_blocks = 0
            new_passes = 0
            if baseline_result is not None:
                for event_id, proposed_passed in proposed_result.event_results.items():
                    baseline_passed = baseline_result.event_results.get(event_id, True)
                    if not proposed_passed and baseline_passed:
                        new_blocks += 1
                    elif proposed_passed and not baseline_passed:
                        new_passes += 1
            else:
                # No baseline → everything blocked by proposed is a "new block"
                new_blocks = proposed_result.blocked_events

            trace_results.append(
                TraceSimulationResult(
                    trace_id=trace.trace_id,
                    proposed_result=proposed_result,
                    baseline_result=baseline_result,
                    new_blocks=new_blocks,
                    new_passes=new_passes,
                )
            )

            total_events += trace.event_count
            would_block_count += proposed_result.blocked_events
            baseline_block_count += (
                baseline_result.blocked_events if baseline_result else 0
            )
            new_blocks_total += new_blocks

        # false_positive_rate: fraction of baseline-passing events newly blocked
        baseline_passing = total_events - baseline_block_count
        false_positive_rate = (
            new_blocks_total / baseline_passing if baseline_passing > 0 else 0.0
        )

        # impact_score: how much more restrictive the proposed policy is (0.0-1.0)
        if total_events > 0:
            impact_score = min(
                abs(would_block_count - baseline_block_count) / total_events, 1.0
            )
        else:
            impact_score = 0.0

        return SimulationReport(
            label=config.label,
            proposed_policy_name=config.proposed_policy.name,
            baseline_policy_name=(
                config.baseline_policy.name if config.baseline_policy else "(none)"
            ),
            trace_results=trace_results,
            total_events=total_events,
            would_block_count=would_block_count,
            baseline_block_count=baseline_block_count,
            false_positive_rate=round(false_positive_rate, 4),
            impact_score=round(impact_score, 4),
        )

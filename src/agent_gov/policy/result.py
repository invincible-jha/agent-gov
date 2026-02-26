"""EvaluationReport — the output of running a policy against an action."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from agent_gov.policy.rule import RuleVerdict


@dataclass
class EvaluationReport:
    """Complete result of evaluating a single action against a policy.

    Attributes
    ----------
    policy_name:
        Name of the :class:`~agent_gov.policy.schema.PolicyConfig` that
        generated this report.
    action:
        The original action dictionary that was evaluated.
    verdicts:
        One :class:`~agent_gov.policy.rule.RuleVerdict` per enabled rule
        that was evaluated.
    passed:
        ``True`` only when *all* verdicts report ``passed=True``.
    timestamp:
        UTC datetime at which the evaluation completed.
    """

    policy_name: str
    action: dict[str, object]
    verdicts: list[RuleVerdict] = field(default_factory=list)
    passed: bool = True
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def failed_verdicts(self) -> list[RuleVerdict]:
        """Return only the verdicts that did not pass."""
        return [v for v in self.verdicts if not v.passed]

    @property
    def passed_verdicts(self) -> list[RuleVerdict]:
        """Return only the verdicts that passed."""
        return [v for v in self.verdicts if v.passed]

    @property
    def violation_count(self) -> int:
        """Number of rules that flagged a violation."""
        return len(self.failed_verdicts)

    @property
    def highest_severity(self) -> str:
        """Return the highest severity among all failed verdicts.

        Returns ``"none"`` when there are no failures.
        """
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
        if not self.failed_verdicts:
            return "none"
        return max(
            (v.severity for v in self.failed_verdicts),
            key=lambda s: severity_order.get(s, 0),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise the report to a plain dictionary."""
        return {
            "policy_name": self.policy_name,
            "action": self.action,
            "passed": self.passed,
            "timestamp": self.timestamp.isoformat(),
            "violation_count": self.violation_count,
            "highest_severity": self.highest_severity,
            "verdicts": [v.to_dict() for v in self.verdicts],
        }

    def summary(self) -> str:
        """Return a one-line human-readable summary."""
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] policy={self.policy_name!r} "
            f"violations={self.violation_count} "
            f"highest_severity={self.highest_severity}"
        )

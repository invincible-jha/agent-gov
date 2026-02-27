"""Compliance posture scorer.

Computes aggregate compliance scores from a list of :class:`EvidenceEntry`
objects.  Scores are expressed as floats in the range [0, 100].

The scoring model is intentionally straightforward (pass-count / total)
so it remains auditable and deterministic — no ML weights, no proprietary
algorithms.

Usage
-----
::

    from agent_gov.dashboard.evidence_collector import EvidenceEntry
    from agent_gov.dashboard.posture_scorer import PostureScorer

    scorer = PostureScorer()
    score = scorer.score(entries)
    print(score.overall_score)  # 0.0 – 100.0
    print(score.per_policy)     # {"eu-ai-act": 85.0, ...}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_gov.dashboard.evidence_collector import EvidenceEntry


@dataclass(frozen=True)
class PostureScore:
    """Compliance posture score computed from evidence.

    Parameters
    ----------
    overall_score:
        Aggregate score across all policies/rules (0–100).
    per_policy:
        Mapping of policy_id to pass-rate score (0–100).
    total_entries:
        Total number of evidence entries analysed.
    pass_count:
        Number of entries with result ``"pass"``.
    fail_count:
        Number of entries with result ``"fail"``.
    skip_count:
        Number of entries with result ``"skip"``.
    computed_at:
        UTC timestamp when the score was computed.
    """

    overall_score: float
    per_policy: dict[str, float]
    total_entries: int
    pass_count: int
    fail_count: int
    skip_count: int
    computed_at: datetime

    def grade(self) -> str:
        """Return a letter-grade interpretation of the overall score.

        Returns
        -------
        str
            One of ``"A"``, ``"B"``, ``"C"``, ``"D"``, ``"F"``.
        """
        score = self.overall_score
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary.

        Returns
        -------
        dict[str, object]
        """
        return {
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade(),
            "per_policy": {k: round(v, 2) for k, v in self.per_policy.items()},
            "total_entries": self.total_entries,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "skip_count": self.skip_count,
            "computed_at": self.computed_at.isoformat(),
        }


class PostureScorer:
    """Computes compliance posture scores from evidence entries.

    Scoring model
    -------------
    * Skip entries are excluded from the denominator (they neither pass
      nor fail — they were not evaluated).
    * ``overall_score = (pass_count / evaluated_count) * 100`` where
      ``evaluated_count = pass_count + fail_count``.
    * When ``evaluated_count == 0``, the score is ``0.0``.
    * Per-policy scores follow the same formula restricted to that policy.

    Parameters
    ----------
    skip_weight:
        Weight applied to skip results when included in denominator.
        Defaults to ``0.0`` (skips are excluded from scoring).
    """

    def __init__(self, skip_weight: float = 0.0) -> None:
        if not (0.0 <= skip_weight <= 1.0):
            raise ValueError(f"skip_weight must be in [0, 1], got {skip_weight}")
        self._skip_weight = skip_weight

    def score(self, evidence: list[EvidenceEntry]) -> PostureScore:
        """Compute compliance posture from *evidence*.

        Parameters
        ----------
        evidence:
            List of :class:`~agent_gov.dashboard.evidence_collector.EvidenceEntry`
            objects to score.

        Returns
        -------
        PostureScore
            Aggregate and per-policy scores.
        """
        pass_count = sum(1 for e in evidence if e.result == "pass")
        fail_count = sum(1 for e in evidence if e.result == "fail")
        skip_count = sum(1 for e in evidence if e.result == "skip")

        overall = self._compute_score(pass_count, fail_count, skip_count)

        # Group by policy
        policy_groups: dict[str, list[EvidenceEntry]] = {}
        for entry in evidence:
            policy_groups.setdefault(entry.policy_id, []).append(entry)

        per_policy: dict[str, float] = {}
        for policy_id, group in policy_groups.items():
            p = sum(1 for e in group if e.result == "pass")
            f = sum(1 for e in group if e.result == "fail")
            s = sum(1 for e in group if e.result == "skip")
            per_policy[policy_id] = self._compute_score(p, f, s)

        return PostureScore(
            overall_score=overall,
            per_policy=per_policy,
            total_entries=len(evidence),
            pass_count=pass_count,
            fail_count=fail_count,
            skip_count=skip_count,
            computed_at=datetime.now(tz=timezone.utc),
        )

    def score_trend(
        self, evidence_windows: list[list[EvidenceEntry]]
    ) -> list[float]:
        """Compute a trend of overall scores across multiple evidence windows.

        Parameters
        ----------
        evidence_windows:
            Ordered list of evidence slices (e.g. one per day).

        Returns
        -------
        list[float]
            Overall score for each window, in the same order.
        """
        return [self.score(window).overall_score for window in evidence_windows]

    def _compute_score(
        self, pass_count: int, fail_count: int, skip_count: int
    ) -> float:
        """Internal score computation."""
        weighted_skip = skip_count * self._skip_weight
        denominator = pass_count + fail_count + weighted_skip
        if denominator == 0:
            return 0.0
        return (pass_count / denominator) * 100.0


__all__ = [
    "PostureScore",
    "PostureScorer",
]

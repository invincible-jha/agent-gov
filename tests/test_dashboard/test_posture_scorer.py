"""Tests for agent_gov.dashboard.posture_scorer."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_gov.dashboard.evidence_collector import EvidenceEntry
from agent_gov.dashboard.posture_scorer import PostureScore, PostureScorer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    result: str,
    policy_id: str = "eu-ai-act",
    rule_id: str = "A13",
) -> EvidenceEntry:
    return EvidenceEntry(
        timestamp=datetime.now(timezone.utc),
        policy_id=policy_id,
        rule_id=rule_id,
        result=result,
        context={},
    )


def _passes(n: int, **kwargs: str) -> list[EvidenceEntry]:
    return [_make_entry("pass", **kwargs) for _ in range(n)]


def _fails(n: int, **kwargs: str) -> list[EvidenceEntry]:
    return [_make_entry("fail", **kwargs) for _ in range(n)]


def _skips(n: int, **kwargs: str) -> list[EvidenceEntry]:
    return [_make_entry("skip", **kwargs) for _ in range(n)]


# ---------------------------------------------------------------------------
# PostureScore tests
# ---------------------------------------------------------------------------


class TestPostureScore:
    def test_frozen(self) -> None:
        score = PostureScore(
            overall_score=85.0,
            per_policy={},
            total_entries=10,
            pass_count=8,
            fail_count=2,
            skip_count=0,
            computed_at=datetime.now(timezone.utc),
        )
        with pytest.raises((AttributeError, TypeError)):
            score.overall_score = 0  # type: ignore[misc]

    def test_grade_a_at_90(self) -> None:
        score = PostureScore(90.0, {}, 10, 9, 1, 0, datetime.now(timezone.utc))
        assert score.grade() == "A"

    def test_grade_a_at_100(self) -> None:
        score = PostureScore(100.0, {}, 10, 10, 0, 0, datetime.now(timezone.utc))
        assert score.grade() == "A"

    def test_grade_b(self) -> None:
        score = PostureScore(85.0, {}, 10, 8, 2, 0, datetime.now(timezone.utc))
        assert score.grade() == "B"

    def test_grade_c(self) -> None:
        score = PostureScore(75.0, {}, 10, 7, 3, 0, datetime.now(timezone.utc))
        assert score.grade() == "C"

    def test_grade_d(self) -> None:
        score = PostureScore(65.0, {}, 10, 6, 4, 0, datetime.now(timezone.utc))
        assert score.grade() == "D"

    def test_grade_f_below_60(self) -> None:
        score = PostureScore(50.0, {}, 10, 5, 5, 0, datetime.now(timezone.utc))
        assert score.grade() == "F"

    def test_to_dict_has_required_keys(self) -> None:
        score = PostureScore(80.0, {"p": 80.0}, 10, 8, 2, 0, datetime.now(timezone.utc))
        d = score.to_dict()
        assert "overall_score" in d
        assert "grade" in d
        assert "per_policy" in d
        assert "total_entries" in d
        assert "pass_count" in d
        assert "fail_count" in d
        assert "skip_count" in d
        assert "computed_at" in d

    def test_to_dict_overall_score_rounded(self) -> None:
        score = PostureScore(83.33333, {}, 10, 8, 2, 0, datetime.now(timezone.utc))
        d = score.to_dict()
        assert d["overall_score"] == round(83.33333, 2)


# ---------------------------------------------------------------------------
# PostureScorer tests
# ---------------------------------------------------------------------------


class TestPostureScorerBasic:
    def test_all_pass_gives_100(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(10)
        result = scorer.score(evidence)
        assert result.overall_score == 100.0

    def test_all_fail_gives_0(self) -> None:
        scorer = PostureScorer()
        evidence = _fails(10)
        result = scorer.score(evidence)
        assert result.overall_score == 0.0

    def test_empty_evidence_gives_0(self) -> None:
        scorer = PostureScorer()
        result = scorer.score([])
        assert result.overall_score == 0.0

    def test_half_pass_half_fail_gives_50(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(5) + _fails(5)
        result = scorer.score(evidence)
        assert result.overall_score == 50.0

    def test_skip_excluded_from_denominator_by_default(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(8) + _fails(2) + _skips(10)
        result = scorer.score(evidence)
        # 8 / (8+2) = 80%
        assert abs(result.overall_score - 80.0) < 0.01

    def test_counts_accurate(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(3) + _fails(2) + _skips(1)
        result = scorer.score(evidence)
        assert result.pass_count == 3
        assert result.fail_count == 2
        assert result.skip_count == 1
        assert result.total_entries == 6

    def test_total_entries_set(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(4)
        result = scorer.score(evidence)
        assert result.total_entries == 4

    def test_computed_at_is_utc(self) -> None:
        scorer = PostureScorer()
        result = scorer.score(_passes(1))
        assert result.computed_at.tzinfo is not None


class TestPostureScorerPerPolicy:
    def test_per_policy_computed(self) -> None:
        scorer = PostureScorer()
        evidence = (
            _passes(4, policy_id="eu-ai-act")
            + _fails(1, policy_id="eu-ai-act")
            + _passes(3, policy_id="gdpr")
        )
        result = scorer.score(evidence)
        assert "eu-ai-act" in result.per_policy
        assert "gdpr" in result.per_policy

    def test_per_policy_eu_ai_act_score(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(8, policy_id="eu-ai-act") + _fails(2, policy_id="eu-ai-act")
        result = scorer.score(evidence)
        assert abs(result.per_policy["eu-ai-act"] - 80.0) < 0.01

    def test_per_policy_all_pass(self) -> None:
        scorer = PostureScorer()
        evidence = _passes(5, policy_id="hipaa")
        result = scorer.score(evidence)
        assert result.per_policy["hipaa"] == 100.0

    def test_per_policy_keys_match_input_policies(self) -> None:
        scorer = PostureScorer()
        evidence = (
            _passes(2, policy_id="eu-ai-act")
            + _passes(2, policy_id="gdpr")
            + _passes(2, policy_id="hipaa")
        )
        result = scorer.score(evidence)
        assert set(result.per_policy.keys()) == {"eu-ai-act", "gdpr", "hipaa"}


class TestPostureScorerWithSkipWeight:
    def test_skip_weight_1_includes_skips(self) -> None:
        scorer = PostureScorer(skip_weight=1.0)
        evidence = _passes(5) + _skips(5)
        # denominator = 5+0+5 = 10; score = 5/10 = 50%
        result = scorer.score(evidence)
        assert abs(result.overall_score - 50.0) < 0.01

    def test_invalid_skip_weight_raises(self) -> None:
        with pytest.raises(ValueError):
            PostureScorer(skip_weight=2.0)

    def test_skip_weight_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            PostureScorer(skip_weight=-0.1)


class TestPostureScorerTrend:
    def test_trend_returns_list_of_scores(self) -> None:
        scorer = PostureScorer()
        windows: list[list[EvidenceEntry]] = [
            _passes(10),
            _passes(7) + _fails(3),
            _passes(5) + _fails(5),
        ]
        trend = scorer.score_trend(windows)
        assert len(trend) == 3
        assert trend[0] == 100.0
        assert abs(trend[1] - 70.0) < 0.01
        assert abs(trend[2] - 50.0) < 0.01

    def test_trend_empty_windows_returns_zeros(self) -> None:
        scorer = PostureScorer()
        trend = scorer.score_trend([[], []])
        assert trend == [0.0, 0.0]

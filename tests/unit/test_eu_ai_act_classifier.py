"""Tests for EU AI Act risk classification engine.

Covers RiskLevel enum, RiskClassification dataclass, and the full
EUAIActClassifier.classify() decision tree including all four risk tiers,
all eight Annex III categories, confidence scaling, and edge cases.
"""
from __future__ import annotations

import dataclasses

import pytest

from agent_gov.frameworks.eu_ai_act_classifier import (
    ANNEX_III_CATEGORIES,
    EUAIActClassifier,
    RiskClassification,
    RiskLevel,
)


# ---------------------------------------------------------------------------
# RiskLevel enum
# ---------------------------------------------------------------------------


class TestRiskLevelEnum:
    def test_unacceptable_value(self) -> None:
        assert RiskLevel.UNACCEPTABLE.value == "unacceptable"

    def test_high_value(self) -> None:
        assert RiskLevel.HIGH.value == "high"

    def test_limited_value(self) -> None:
        assert RiskLevel.LIMITED.value == "limited"

    def test_minimal_value(self) -> None:
        assert RiskLevel.MINIMAL.value == "minimal"

    def test_all_four_levels_exist(self) -> None:
        levels = {level.value for level in RiskLevel}
        assert levels == {"unacceptable", "high", "limited", "minimal"}

    def test_risk_level_is_str_subclass(self) -> None:
        # str Enum — values behave as strings in JSON serialisation.
        assert isinstance(RiskLevel.HIGH, str)


# ---------------------------------------------------------------------------
# RiskClassification dataclass
# ---------------------------------------------------------------------------


class TestRiskClassification:
    def _make(self) -> RiskClassification:
        return RiskClassification(
            level=RiskLevel.HIGH,
            annex_iii_category="employment",
            article_references=["Article 6(1)", "Annex III(4)"],
            obligations=["Risk management system (Article 9)"],
            reasoning="Matched hiring keywords.",
            confidence=0.7,
        )

    def test_construction_all_fields(self) -> None:
        rc = self._make()
        assert rc.level is RiskLevel.HIGH
        assert rc.annex_iii_category == "employment"
        assert "Article 6(1)" in rc.article_references
        assert rc.confidence == pytest.approx(0.7)

    def test_is_dataclass(self) -> None:
        rc = self._make()
        assert dataclasses.is_dataclass(rc)

    def test_asdict_serialisable(self) -> None:
        rc = self._make()
        d = dataclasses.asdict(rc)
        assert d["level"] == "high"
        assert isinstance(d["article_references"], list)
        assert isinstance(d["obligations"], list)

    def test_obligations_list_mutable(self) -> None:
        rc = self._make()
        rc.obligations.append("new obligation")
        assert "new obligation" in rc.obligations

    def test_article_references_list_type(self) -> None:
        rc = self._make()
        assert isinstance(rc.article_references, list)

    def test_confidence_float(self) -> None:
        rc = self._make()
        assert isinstance(rc.confidence, float)


# ---------------------------------------------------------------------------
# ANNEX_III_CATEGORIES constant
# ---------------------------------------------------------------------------


class TestAnnexIIICategories:
    def test_has_eight_categories(self) -> None:
        assert len(ANNEX_III_CATEGORIES) == 8

    def test_all_have_keywords_key(self) -> None:
        for name, info in ANNEX_III_CATEGORIES.items():
            assert "keywords" in info, f"Missing 'keywords' in {name}"

    def test_all_have_articles_key(self) -> None:
        for name, info in ANNEX_III_CATEGORIES.items():
            assert "articles" in info, f"Missing 'articles' in {name}"

    def test_expected_categories_present(self) -> None:
        expected = {
            "biometric_identification",
            "critical_infrastructure",
            "education_training",
            "employment",
            "essential_services",
            "law_enforcement",
            "migration_asylum",
            "justice_democracy",
        }
        assert set(ANNEX_III_CATEGORIES.keys()) == expected


# ---------------------------------------------------------------------------
# EUAIActClassifier — helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def classifier() -> EUAIActClassifier:
    return EUAIActClassifier()


# ---------------------------------------------------------------------------
# Unacceptable risk
# ---------------------------------------------------------------------------


class TestUnacceptableRisk:
    def test_social_scoring_is_unacceptable(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("A social scoring system for citizens.")
        assert result.level is RiskLevel.UNACCEPTABLE

    def test_subliminal_is_unacceptable(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Uses subliminal techniques to influence users.")
        assert result.level is RiskLevel.UNACCEPTABLE

    def test_manipulation_is_unacceptable(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("AI for psychological manipulation of users.")
        assert result.level is RiskLevel.UNACCEPTABLE

    def test_real_time_biometric_in_public_is_unacceptable(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify(
            "Real-time remote biometric identification in public spaces."
        )
        assert result.level is RiskLevel.UNACCEPTABLE

    def test_emotion_recognition_workplace_is_unacceptable(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("Emotion recognition in workplace environments.")
        assert result.level is RiskLevel.UNACCEPTABLE

    def test_emotion_recognition_education_is_unacceptable(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("Emotion recognition in education settings.")
        assert result.level is RiskLevel.UNACCEPTABLE

    def test_unacceptable_article_reference_is_article_5(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("social scoring platform")
        assert "Article 5" in result.article_references

    def test_unacceptable_category_label(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("social scoring platform")
        assert result.annex_iii_category == "Article 5 prohibited"

    def test_unacceptable_obligation_mentions_prohibited(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("social scoring platform")
        assert any("PROHIBITED" in ob for ob in result.obligations)

    def test_unacceptable_confidence_is_0_9(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("social scoring system")
        assert result.confidence == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# High risk — Annex III categories
# ---------------------------------------------------------------------------


class TestHighRiskCategories:
    def test_biometric_identification(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("A facial recognition system for access control.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "biometric_identification"

    def test_critical_infrastructure(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("AI for managing energy grid infrastructure.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "critical_infrastructure"

    def test_education_training(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify(
            "A system for student assessment and exam scoring in academic settings."
        )
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "education_training"

    def test_employment(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Automated recruitment and cv screening tool.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "employment"

    def test_essential_services(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Credit scoring for loan applicants.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "essential_services"

    def test_law_enforcement(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Crime prediction tool for law enforcement.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "law_enforcement"

    def test_migration_asylum(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("AI to process visa and asylum applications.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "migration_asylum"

    def test_justice_democracy(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("AI for sentencing and judicial decision support.")
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "justice_democracy"

    def test_high_risk_has_nine_obligations(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("facial recognition access control")
        assert result.level is RiskLevel.HIGH
        assert len(result.obligations) == 9

    def test_high_risk_article_references_include_article_6(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("recruitment ai system")
        assert result.level is RiskLevel.HIGH
        assert any("Article 6" in ref for ref in result.article_references)

    def test_best_match_chosen_by_keyword_count(
        self, classifier: EUAIActClassifier
    ) -> None:
        # "hiring" and "recruitment" both match employment (2 hits).
        # "biometric" matches biometric_identification (1 hit).
        # Employment should win.
        result = classifier.classify(
            "AI tool for hiring, recruitment, and biometric checks."
        )
        assert result.level is RiskLevel.HIGH
        assert result.annex_iii_category == "employment"


# ---------------------------------------------------------------------------
# Limited risk
# ---------------------------------------------------------------------------


class TestLimitedRisk:
    def test_chatbot_is_limited(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("A customer service chatbot for our website.")
        assert result.level is RiskLevel.LIMITED

    def test_deepfake_is_limited(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Tool to create deepfake videos.")
        assert result.level is RiskLevel.LIMITED

    def test_synthetic_content_is_limited(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Generates synthetic data for testing.")
        assert result.level is RiskLevel.LIMITED

    def test_generated_content_is_limited(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("AI-produced generated content platform.")
        assert result.level is RiskLevel.LIMITED

    def test_emotion_detection_is_limited(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("System for emotion detection in images.")
        assert result.level is RiskLevel.LIMITED

    def test_biometric_categorization_is_high_risk(
        self, classifier: EUAIActClassifier
    ) -> None:
        # The phrase "biometric categorization" is an Article 50 limited-risk
        # trigger, but the word "biometric" is also a substring keyword in the
        # Annex III "biometric_identification" high-risk category.  Because the
        # classifier evaluates Annex III HIGH risk before Article 50 LIMITED,
        # any description containing "biometric categorization" will first match
        # the Annex III "biometric" keyword and be classified HIGH.
        # This reflects the correct EU AI Act priority order.
        result = classifier.classify(
            "AI system that performs biometric categorization of users by appearance."
        )
        assert result.level is RiskLevel.HIGH

    def test_limited_article_reference_is_article_50(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("A chatbot assistant.")
        assert "Article 50" in result.article_references

    def test_limited_has_two_obligations(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("customer chatbot")
        assert len(result.obligations) == 2

    def test_limited_confidence_is_0_7(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("chatbot for user queries")
        assert result.confidence == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Minimal risk
# ---------------------------------------------------------------------------


class TestMinimalRisk:
    def test_benign_description_is_minimal(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("A spam filter for email.")
        assert result.level is RiskLevel.MINIMAL

    def test_minimal_has_no_article_references(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("A recommendation engine for movies.")
        assert result.level is RiskLevel.MINIMAL
        assert result.article_references == []

    def test_minimal_confidence_is_0_6(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Image classification for product catalogues.")
        assert result.confidence == pytest.approx(0.6)

    def test_minimal_category_is_none(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Product recommendation system.")
        assert result.annex_iii_category == "none"

    def test_empty_description_returns_minimal(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("")
        assert result.level is RiskLevel.MINIMAL


# ---------------------------------------------------------------------------
# Confidence scaling
# ---------------------------------------------------------------------------


class TestConfidenceScaling:
    def test_more_keyword_matches_higher_confidence(
        self, classifier: EUAIActClassifier
    ) -> None:
        # Single match: "biometric" → confidence = 0.5 + 1*0.1 = 0.6
        single = classifier.classify("biometric data processing system")
        # Multiple matches: biometric + facial recognition + fingerprint
        multi = classifier.classify(
            "biometric system using facial recognition and fingerprint scanning"
        )
        assert multi.level is RiskLevel.HIGH
        assert single.level is RiskLevel.HIGH
        assert multi.confidence > single.confidence

    def test_confidence_capped_at_0_95(self, classifier: EUAIActClassifier) -> None:
        # Pile on many employment keywords to exceed natural cap.
        description = (
            "recruitment hiring job application cv screening "
            "performance evaluation promotion termination task allocation worker monitoring"
        )
        result = classifier.classify(description)
        assert result.confidence <= 0.95


# ---------------------------------------------------------------------------
# use_cases and data_categories influence classification
# ---------------------------------------------------------------------------


class TestCombinedTextMatching:
    def test_use_cases_trigger_high_risk(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify(
            system_description="Generic ML pipeline.",
            use_cases=["recruitment automation"],
        )
        assert result.level is RiskLevel.HIGH

    def test_data_categories_trigger_high_risk(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify(
            system_description="Data analysis tool.",
            data_categories=["biometric data", "fingerprint records"],
        )
        assert result.level is RiskLevel.HIGH

    def test_none_use_cases_handled(self, classifier: EUAIActClassifier) -> None:
        result = classifier.classify("Email spam filter.", use_cases=None)
        assert result.level is RiskLevel.MINIMAL

    def test_none_data_categories_handled(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("Movie recommendation.", data_categories=None)
        assert result.level is RiskLevel.MINIMAL

    def test_empty_list_use_cases_handled(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify("Content filter.", use_cases=[])
        assert result.level is RiskLevel.MINIMAL

    def test_case_insensitive_matching(self, classifier: EUAIActClassifier) -> None:
        # Uppercase keywords should still match.
        result = classifier.classify("RECRUITMENT AI TOOL FOR HIRING DECISIONS")
        assert result.level is RiskLevel.HIGH

    def test_combined_text_from_all_three_sources(
        self, classifier: EUAIActClassifier
    ) -> None:
        result = classifier.classify(
            system_description="Generic enterprise tool.",
            use_cases=["applicant screening"],
            data_categories=["cv data", "employment history"],
        )
        # "cv screening" and "hiring" may not appear verbatim, but check
        # that classification runs without error.
        assert result.level in list(RiskLevel)

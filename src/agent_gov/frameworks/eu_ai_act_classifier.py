"""EU AI Act risk classification per Annex III.

Classifies AI systems into one of four risk categories as defined by
Regulation (EU) 2024/1689 (the EU AI Act):

- UNACCEPTABLE: Prohibited practices under Article 5.
- HIGH: Annex III high-risk applications.
- LIMITED: Transparency obligations under Article 50.
- MINIMAL: No mandatory obligations.

Example
-------
::

    from agent_gov.frameworks.eu_ai_act_classifier import EUAIActClassifier

    classifier = EUAIActClassifier()
    result = classifier.classify(
        system_description="A CV screening tool for job applicants",
        use_cases=["hiring", "recruitment automation"],
        data_categories=["employment history", "personal data"],
    )
    print(result.level)        # RiskLevel.HIGH
    print(result.obligations)  # List of mandatory obligations
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    """EU AI Act risk categories per Regulation (EU) 2024/1689."""

    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


@dataclass
class RiskClassification:
    """Result of EU AI Act risk classification.

    Attributes
    ----------
    level:
        The determined risk level for the AI system.
    annex_iii_category:
        The matched Annex III category name, or a descriptive label for
        unacceptable/limited/minimal outcomes.
    article_references:
        List of EU AI Act article references applicable to this classification.
    obligations:
        Human-readable list of mandatory compliance obligations.
    reasoning:
        Explanation of why this classification was assigned.
    confidence:
        Confidence score between 0.0 and 1.0.  Higher values indicate more
        keyword matches and thus a stronger signal.
    """

    level: RiskLevel
    annex_iii_category: str
    article_references: list[str]
    obligations: list[str]
    reasoning: str
    confidence: float


# ---------------------------------------------------------------------------
# Annex III high-risk category definitions
# ---------------------------------------------------------------------------

#: Mapping of Annex III category name → keyword triggers and article refs.
#: Each category corresponds to one of the eight Annex III domains.
ANNEX_III_CATEGORIES: dict[str, dict[str, list[str]]] = {
    "biometric_identification": {
        "keywords": [
            "biometric",
            "facial recognition",
            "fingerprint",
            "iris scan",
            "voice identification",
            "gait analysis",
        ],
        "articles": ["Article 6(1)", "Annex III(1)"],
    },
    "critical_infrastructure": {
        "keywords": [
            "infrastructure",
            "energy",
            "water supply",
            "gas",
            "heating",
            "traffic management",
            "digital infrastructure",
        ],
        "articles": ["Article 6(1)", "Annex III(2)"],
    },
    "education_training": {
        "keywords": [
            "education",
            "admission",
            "student assessment",
            "exam scoring",
            "learning outcome",
            "academic",
            "school",
            "university",
        ],
        "articles": ["Article 6(1)", "Annex III(3)"],
    },
    "employment": {
        "keywords": [
            "recruitment",
            "hiring",
            "job application",
            "cv screening",
            "performance evaluation",
            "promotion",
            "termination",
            "task allocation",
            "worker monitoring",
        ],
        "articles": ["Article 6(1)", "Annex III(4)"],
    },
    "essential_services": {
        "keywords": [
            "credit scoring",
            "insurance",
            "social benefit",
            "emergency services",
            "health insurance",
            "creditworthiness",
        ],
        "articles": ["Article 6(1)", "Annex III(5)"],
    },
    "law_enforcement": {
        "keywords": [
            "law enforcement",
            "criminal",
            "polygraph",
            "evidence",
            "suspect",
            "crime prediction",
            "profiling",
        ],
        "articles": ["Article 6(1)", "Annex III(6)"],
    },
    "migration_asylum": {
        "keywords": [
            "migration",
            "asylum",
            "visa",
            "border control",
            "residence permit",
            "immigration",
        ],
        "articles": ["Article 6(1)", "Annex III(7)"],
    },
    "justice_democracy": {
        "keywords": [
            "judicial",
            "court",
            "legal interpretation",
            "sentencing",
            "dispute resolution",
            "election",
            "voting",
        ],
        "articles": ["Article 6(1)", "Annex III(8)"],
    },
}

#: Article 5 prohibited practices — trigger UNACCEPTABLE classification.
_UNACCEPTABLE_KEYWORDS: list[str] = [
    "social scoring",
    "subliminal",
    "manipulation",
    "real-time remote biometric identification in public",
    "emotion recognition in workplace",
    "emotion recognition in education",
]

#: Article 50 transparency triggers — trigger LIMITED classification.
_LIMITED_KEYWORDS: list[str] = [
    "chatbot",
    "deepfake",
    "synthetic",
    "generated content",
    "emotion detection",
    "biometric categorization",
]

#: Mandatory obligations for Annex III (HIGH risk) systems.
_HIGH_RISK_OBLIGATIONS: list[str] = [
    "Risk management system (Article 9)",
    "Data governance (Article 10)",
    "Technical documentation (Article 11, Annex IV)",
    "Record-keeping / logging (Article 12)",
    "Transparency to users (Article 13)",
    "Human oversight (Article 14)",
    "Accuracy, robustness, cybersecurity (Article 15)",
    "Conformity assessment (Article 43)",
    "Post-market monitoring (Article 72)",
]


class EUAIActClassifier:
    """Classify an AI system's risk level per the EU AI Act.

    Classification proceeds in priority order:

    1. Unacceptable risk (Article 5 prohibited practices).
    2. High risk (Annex III categories).
    3. Limited risk (Article 50 transparency obligations).
    4. Minimal risk (no mandatory obligations).

    The classifier performs case-insensitive keyword matching across the
    combined text of ``system_description``, ``use_cases``, and
    ``data_categories``.
    """

    def classify(
        self,
        system_description: str,
        use_cases: list[str] | None = None,
        data_categories: list[str] | None = None,
    ) -> RiskClassification:
        """Determine the risk level of an AI system.

        Parameters
        ----------
        system_description:
            Free-text description of the AI system and its purpose.
        use_cases:
            Optional list of intended use-case strings.  These are included
            in the keyword search corpus alongside ``system_description``.
        data_categories:
            Optional list of data category strings (e.g. ``"biometric data"``,
            ``"financial data"``).  Also included in the search corpus.

        Returns
        -------
        RiskClassification
            The determined risk classification with obligations and reasoning.
        """
        description_lower = system_description.lower()
        use_case_text = " ".join(use_cases or []).lower()
        data_text = " ".join(data_categories or []).lower()
        combined_text = f"{description_lower} {use_case_text} {data_text}"

        # 1. Check for unacceptable risk (Article 5 prohibited practices).
        for keyword in _UNACCEPTABLE_KEYWORDS:
            if keyword in combined_text:
                return RiskClassification(
                    level=RiskLevel.UNACCEPTABLE,
                    annex_iii_category="Article 5 prohibited",
                    article_references=["Article 5"],
                    obligations=[
                        "PROHIBITED — This AI system may not be placed on the market."
                    ],
                    reasoning=f"System matches prohibited practice: '{keyword}'",
                    confidence=0.9,
                )

        # 2. Check for high-risk (Annex III categories).
        matched_categories: list[tuple[str, int]] = []
        for cat_name, cat_info in ANNEX_III_CATEGORIES.items():
            match_count = sum(
                1 for kw in cat_info["keywords"] if kw in combined_text
            )
            if match_count > 0:
                matched_categories.append((cat_name, match_count))

        if matched_categories:
            best_match = max(matched_categories, key=lambda x: x[1])
            cat_name = best_match[0]
            cat_info = ANNEX_III_CATEGORIES[cat_name]
            return RiskClassification(
                level=RiskLevel.HIGH,
                annex_iii_category=cat_name,
                article_references=cat_info["articles"],
                obligations=_HIGH_RISK_OBLIGATIONS,
                reasoning=(
                    f"System matches Annex III category '{cat_name}' "
                    f"with {best_match[1]} keyword matches."
                ),
                confidence=min(0.5 + best_match[1] * 0.1, 0.95),
            )

        # 3. Check for limited risk (Article 50 transparency obligations).
        for keyword in _LIMITED_KEYWORDS:
            if keyword in combined_text:
                return RiskClassification(
                    level=RiskLevel.LIMITED,
                    annex_iii_category="Article 50 transparency",
                    article_references=["Article 50"],
                    obligations=[
                        "Inform users they are interacting with AI (Article 50(1))",
                        "Mark AI-generated content as such (Article 50(2))",
                    ],
                    reasoning=(
                        f"System requires transparency per Article 50: '{keyword}'"
                    ),
                    confidence=0.7,
                )

        # 4. Minimal risk — no mandatory obligations.
        return RiskClassification(
            level=RiskLevel.MINIMAL,
            annex_iii_category="none",
            article_references=[],
            obligations=[
                "No mandatory obligations. Voluntary codes of conduct encouraged."
            ],
            reasoning="No high-risk or limited-risk indicators found.",
            confidence=0.6,
        )

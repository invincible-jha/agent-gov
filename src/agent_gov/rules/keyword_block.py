"""Keyword blocking rule — reject actions containing specific terms.

Scans all string values in the action dictionary for blocked keywords using
exact-match and case-insensitive substring matching.  No regex or ML is used.

Configuration parameters
------------------------
keywords : list[str]
    List of words or phrases to block.  Required.
case_sensitive : bool
    When ``True``, matching is case-sensitive.  Defaults to ``False``
    (case-insensitive matching).
match_whole_word : bool
    When ``True``, only match complete words (space/punctuation boundaries).
    Defaults to ``False`` (substring match).

Example config
--------------
.. code-block:: yaml

    type: keyword_block
    params:
      keywords:
        - "delete all"
        - "drop table"
        - "truncate"
      case_sensitive: false
      match_whole_word: false
"""
from __future__ import annotations

import re
import string

from agent_gov.policy.rule import PolicyRule, RuleVerdict


class KeywordBlockRule(PolicyRule):
    """Block agent actions containing specific keywords or phrases.

    Rule type name: ``keyword_block``
    """

    name: str = "keyword_block"

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        """Search action string values for blocked keywords.

        Parameters
        ----------
        action:
            Arbitrary action dict.  All string values (recursive) are scanned.
        config:
            Supported keys: ``keywords`` (list[str]), ``case_sensitive`` (bool),
            ``match_whole_word`` (bool).

        Returns
        -------
        RuleVerdict
            ``passed=False`` when any blocked keyword is found.
        """
        raw_keywords = config.get("keywords", [])
        if not isinstance(raw_keywords, list):
            raw_keywords = [str(raw_keywords)]
        keywords: list[str] = [str(k) for k in raw_keywords]

        case_sensitive: bool = bool(config.get("case_sensitive", False))
        match_whole_word: bool = bool(config.get("match_whole_word", False))

        if not keywords:
            return RuleVerdict(
                rule_name=self.name,
                passed=True,
                severity="medium",
                message="No keywords configured — check passes by default.",
            )

        all_strings = _extract_strings(action)
        blocked_matches: list[dict[str, str]] = []

        for field_path, text in all_strings:
            for keyword in keywords:
                if _matches(text, keyword, case_sensitive=case_sensitive, whole_word=match_whole_word):
                    blocked_matches.append({"field": field_path, "keyword": keyword})

        if not blocked_matches:
            return RuleVerdict(
                rule_name=self.name,
                passed=True,
                severity="medium",
                message="No blocked keywords detected.",
            )

        blocked_keywords = sorted({m["keyword"] for m in blocked_matches})
        return RuleVerdict(
            rule_name=self.name,
            passed=False,
            severity="high",
            message=(
                f"Blocked keyword(s) found: {blocked_keywords!r}. "
                f"{len(blocked_matches)} match(es) across {len({m['field'] for m in blocked_matches})} field(s)."
            ),
            details={
                "blocked_keywords": blocked_keywords,
                "matches": blocked_matches,
            },
        )

    def validate_config(self, config: dict[str, object]) -> list[str]:
        """Validate that ``keywords`` is a non-empty list."""
        errors: list[str] = []
        keywords = config.get("keywords")
        if keywords is None:
            errors.append("keyword_block: 'keywords' is not configured.")
        elif not isinstance(keywords, list):
            errors.append(
                f"keyword_block: 'keywords' must be a list, got {type(keywords).__name__}."
            )
        elif not keywords:
            errors.append("keyword_block: 'keywords' list must not be empty.")
        return errors


def _extract_strings(
    data: dict[str, object],
    prefix: str = "",
) -> list[tuple[str, str]]:
    """Recursively extract (field_path, string_value) pairs from a dict."""
    results: list[tuple[str, str]] = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, str):
            results.append((path, value))
        elif isinstance(value, dict):
            results.extend(_extract_strings(value, path))
        elif isinstance(value, list):
            results.extend(_extract_strings_from_list(value, path))
    return results


def _extract_strings_from_list(
    data: list[object],
    prefix: str,
) -> list[tuple[str, str]]:
    """Recursively extract strings from a list."""
    results: list[tuple[str, str]] = []
    for index, item in enumerate(data):
        path = f"{prefix}[{index}]"
        if isinstance(item, str):
            results.append((path, item))
        elif isinstance(item, dict):
            results.extend(_extract_strings(item, path))
        elif isinstance(item, list):
            results.extend(_extract_strings_from_list(item, path))
    return results


def _matches(
    text: str,
    keyword: str,
    *,
    case_sensitive: bool,
    whole_word: bool,
) -> bool:
    """Return True when ``keyword`` is found in ``text``."""
    compare_text = text if case_sensitive else text.lower()
    compare_keyword = keyword if case_sensitive else keyword.lower()

    if not whole_word:
        return compare_keyword in compare_text

    # Whole-word matching: keyword must be surrounded by non-word characters
    # or start/end of string.
    word_boundary = re.compile(
        r"(?<![A-Za-z0-9_])" + re.escape(compare_keyword) + r"(?![A-Za-z0-9_])"
    )
    return bool(word_boundary.search(compare_text))

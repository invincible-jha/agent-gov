"""PII detection rule using regex patterns.

Detects common personally identifiable information patterns within the string
values of an action dictionary.  Detection is regex-based — no ML model is used.

Supported patterns
------------------
- US Social Security Numbers (``SSN``)
- Credit / debit card numbers (Luhn-unchecked 13–16 digit sequences)
- Email addresses (RFC 5322 simplified)
- US phone numbers (various formatting styles)

Configuration parameters (all optional, default ``True``)
----------------------------------------------------------
check_ssn : bool
    Enable SSN pattern detection.
check_credit_card : bool
    Enable credit card number detection.
check_email : bool
    Enable email address detection.
check_phone : bool
    Enable phone number detection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from agent_gov.policy.rule import PolicyRule, RuleVerdict

# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

# SSN: 3 digits – 2 digits – 4 digits with various separators
_SSN_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[-\s](?!00)\d{2}[-\s](?!0000)\d{4}\b"
)

# Credit card: 13–16 digits, optionally grouped with spaces or hyphens
_CREDIT_CARD_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:\d[ \-]?){13,15}\d\b"
)

# Email: simplified RFC 5322
_EMAIL_PATTERN: re.Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# US Phone: supports (NXX) NXX-XXXX, NXX-NXX-XXXX, +1 variants, dot separators
_PHONE_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:\+?1[-.\s]?)?"
    r"(?:\(?\d{3}\)?[-.\s]?)"
    r"\d{3}[-.\s]?\d{4}\b"
)


@dataclass
class _PiiMatch:
    pattern_name: str
    matched_value: str
    field_path: str


class PiiCheckRule(PolicyRule):
    """Detect PII in action field values using regular expressions.

    The rule walks all string values in the action dictionary (one level deep)
    and flags any that match the enabled PII patterns.

    Rule type name: ``pii_check``
    """

    name: str = "pii_check"

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        """Scan action values for PII patterns.

        Parameters
        ----------
        action:
            The agent action to inspect.
        config:
            Supported keys: ``check_ssn``, ``check_credit_card``,
            ``check_email``, ``check_phone`` (all ``bool``, default ``True``).

        Returns
        -------
        RuleVerdict
            ``passed=False`` when any PII pattern is detected.
        """
        check_ssn: bool = bool(config.get("check_ssn", True))
        check_credit_card: bool = bool(config.get("check_credit_card", True))
        check_email: bool = bool(config.get("check_email", True))
        check_phone: bool = bool(config.get("check_phone", True))

        active_patterns: list[tuple[str, re.Pattern[str]]] = []
        if check_ssn:
            active_patterns.append(("ssn", _SSN_PATTERN))
        if check_credit_card:
            active_patterns.append(("credit_card", _CREDIT_CARD_PATTERN))
        if check_email:
            active_patterns.append(("email", _EMAIL_PATTERN))
        if check_phone:
            active_patterns.append(("phone", _PHONE_PATTERN))

        matches: list[_PiiMatch] = []
        self._scan_dict(action, active_patterns, "", matches)

        if not matches:
            return RuleVerdict(
                rule_name=self.name,
                passed=True,
                severity="medium",
                message="No PII detected.",
            )

        detected_types = sorted({m.pattern_name for m in matches})
        return RuleVerdict(
            rule_name=self.name,
            passed=False,
            severity="high",
            message=(
                f"PII detected in action: {', '.join(detected_types)}. "
                f"Found {len(matches)} match(es)."
            ),
            details={
                "detected_types": detected_types,
                "match_count": len(matches),
                "fields": [m.field_path for m in matches],
            },
        )

    def _scan_dict(
        self,
        data: dict[str, object],
        patterns: list[tuple[str, re.Pattern[str]]],
        prefix: str,
        matches: list[_PiiMatch],
    ) -> None:
        """Recursively scan string values in a dict for PII patterns."""
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, str):
                self._scan_string(value, path, patterns, matches)
            elif isinstance(value, dict):
                self._scan_dict(value, patterns, path, matches)
            elif isinstance(value, list):
                self._scan_list(value, path, patterns, matches)

    def _scan_list(
        self,
        data: list[object],
        prefix: str,
        patterns: list[tuple[str, re.Pattern[str]]],
        matches: list[_PiiMatch],
    ) -> None:
        """Scan list elements for PII patterns."""
        for index, item in enumerate(data):
            path = f"{prefix}[{index}]"
            if isinstance(item, str):
                self._scan_string(item, path, patterns, matches)
            elif isinstance(item, dict):
                self._scan_dict(item, patterns, path, matches)

    def _scan_string(
        self,
        text: str,
        field_path: str,
        patterns: list[tuple[str, re.Pattern[str]]],
        matches: list[_PiiMatch],
    ) -> None:
        """Apply all active patterns to a single string value."""
        for pattern_name, pattern in patterns:
            for match in pattern.finditer(text):
                matches.append(
                    _PiiMatch(
                        pattern_name=pattern_name,
                        matched_value=match.group(),
                        field_path=field_path,
                    )
                )

    def validate_config(self, config: dict[str, object]) -> list[str]:
        """Validate that all config keys are recognised boolean flags."""
        known_keys = {"check_ssn", "check_credit_card", "check_email", "check_phone"}
        errors: list[str] = []
        for key in config:
            if key not in known_keys:
                errors.append(f"Unknown config key {key!r} for pii_check rule.")
        return errors

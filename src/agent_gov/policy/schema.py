"""Pydantic v2 schemas for policy configuration.

These models define the structure of YAML policy files loaded at runtime.
All runtime validation at system boundaries uses these models.

Example YAML structure::

    name: my-policy
    version: "1.0"
    description: "Example policy"
    rules:
      - name: block-pii
        type: pii_check
        severity: high
        params:
          check_email: true
          check_ssn: true
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for policy rule violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleConfig(BaseModel):
    """Configuration for a single policy rule.

    Attributes
    ----------
    name:
        Human-readable label for this rule instance within the policy.
    type:
        Matches the ``PolicyRule.name`` class attribute — used for rule lookup.
    enabled:
        When ``False`` the rule is skipped during evaluation.
    severity:
        Default severity applied to verdicts from this rule.
    params:
        Arbitrary key/value parameters forwarded to the rule's ``evaluate`` call.
    """

    name: str
    type: str
    enabled: bool = True
    severity: Severity = Severity.MEDIUM
    params: dict[str, object] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class PolicyConfig(BaseModel):
    """Top-level policy configuration loaded from a YAML file.

    Attributes
    ----------
    name:
        Unique identifier for this policy.
    version:
        Semantic version string for tracking policy changes.
    description:
        Free-text description of what this policy governs.
    rules:
        Ordered list of rule configurations to evaluate.
    metadata:
        Arbitrary string key/value metadata (author, team, ticket, etc.).
    """

    name: str
    version: str = "1.0"
    description: str = ""
    rules: list[RuleConfig] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @property
    def enabled_rules(self) -> list[RuleConfig]:
        """Return only the rules that are enabled."""
        return [rule for rule in self.rules if rule.enabled]

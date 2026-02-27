"""Pydantic v2 schema for the policy library YAML format.

This schema is used exclusively for the curated governance policy library
located in the ``policies/`` directory at the repository root. It is
distinct from the runtime ``agent_gov.policy.schema`` which defines the
operational policy engine's YAML format.

Library policy YAML structure::

    id: hipaa-phi-protection
    name: HIPAA PHI Protection
    version: "1.0"
    domain: healthcare
    description: |
      Multi-line description of what this policy enforces.
    severity: critical
    rules:
      - id: phi-ssn-block
        name: Block SSN in Output
        condition: regex_match
        parameters:
          pattern: "\\\\b\\\\d{3}-\\\\d{2}-\\\\d{4}\\\\b"
          target: output
        action: block
        message: "Output contains a Social Security Number."
    references:
      - "https://example.com/standard"
    tags:
      - hipaa
      - phi
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LibraryDomain(str, Enum):
    """Compliance domain for a library policy."""

    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EU_AI_ACT = "eu-ai-act"
    GENERAL = "general"
    GDPR = "gdpr"


class LibrarySeverity(str, Enum):
    """Severity level for a library policy."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LibraryRuleAction(str, Enum):
    """Action taken when a library policy rule is triggered."""

    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    REDACT = "redact"


class LibraryRuleConfig(BaseModel):
    """Configuration for a single rule within a library policy.

    Attributes
    ----------
    id:
        Unique identifier for this rule within the policy.
    name:
        Human-readable name for this rule.
    condition:
        Condition type such as ``keyword_block``, ``regex_match``,
        ``cost_limit``, ``rate_limit``, or ``output_length``.
    parameters:
        Arbitrary key/value parameters specific to the condition type.
    action:
        Action to take when the condition triggers.
    message:
        Human-readable violation message shown when this rule fires.
    """

    id: str
    name: str
    condition: str
    parameters: dict[str, object] = Field(default_factory=dict)
    action: LibraryRuleAction
    message: str

    model_config = {"extra": "allow"}


class LibraryPolicyConfig(BaseModel):
    """Top-level schema for a library governance policy YAML file.

    Attributes
    ----------
    id:
        Globally unique identifier for this policy (e.g. ``hipaa-phi-protection``).
    name:
        Human-readable display name.
    version:
        Semantic version string for the policy definition.
    domain:
        Compliance domain this policy belongs to.
    description:
        Multi-line description of what this policy enforces.
    severity:
        Default severity level for violations of this policy.
    rules:
        Ordered list of rule configurations within this policy.
    references:
        List of URLs or standard citations supporting this policy.
    tags:
        Free-form tags for filtering and discovery.
    """

    id: str
    name: str
    version: str = "1.0"
    domain: LibraryDomain
    description: str = ""
    severity: LibrarySeverity
    rules: list[LibraryRuleConfig] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

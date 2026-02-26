"""Abstract base class for policy rules.

All built-in and custom rules must subclass :class:`PolicyRule` and implement
the :meth:`~PolicyRule.evaluate` method.

Example
-------
::

    from agent_gov.policy.rule import PolicyRule, RuleVerdict

    class MyRule(PolicyRule):
        name = "my_rule"

        def evaluate(
            self,
            action: dict[str, object],
            config: dict[str, object],
        ) -> RuleVerdict:
            allowed = action.get("type") == "read"
            return RuleVerdict(
                rule_name=self.name,
                passed=allowed,
                severity="medium",
                message="Only read actions are allowed." if not allowed else "",
            )
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RuleVerdict:
    """Result returned by a single rule evaluation.

    Attributes
    ----------
    rule_name:
        The name of the rule that produced this verdict.
    passed:
        ``True`` when the action satisfies the rule; ``False`` when it violates it.
    severity:
        String severity level (matches :class:`~agent_gov.policy.schema.Severity`
        values: ``"low"``, ``"medium"``, ``"high"``, ``"critical"``).
    message:
        Human-readable explanation, typically set when ``passed`` is ``False``.
    details:
        Arbitrary structured data providing additional context for the verdict.
    """

    rule_name: str = ""
    passed: bool = True
    severity: str = "medium"
    message: str = ""
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise verdict to a plain dictionary."""
        return {
            "rule_name": self.rule_name,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


class PolicyRule(ABC):
    """Abstract base class that all policy rules must implement.

    Class Attributes
    ----------------
    name:
        Unique string identifier for this rule type.  Used to match
        :attr:`~agent_gov.policy.schema.RuleConfig.type` during rule lookup.
        Subclasses must override this attribute.
    """

    name: str = ""

    @abstractmethod
    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        """Evaluate an agent action against this rule.

        Parameters
        ----------
        action:
            Arbitrary key/value dictionary describing the agent action being
            evaluated.  The keys available depend on the calling system.
        config:
            The ``params`` dict from the matching
            :class:`~agent_gov.policy.schema.RuleConfig` instance.

        Returns
        -------
        RuleVerdict
            The result of this rule's evaluation.
        """

    def validate_config(self, config: dict[str, object]) -> list[str]:
        """Validate the rule's configuration parameters.

        Override this method to provide config validation at policy load time.
        Return a list of human-readable error strings; an empty list means the
        config is valid.

        Parameters
        ----------
        config:
            The ``params`` dict from the matching
            :class:`~agent_gov.policy.schema.RuleConfig` instance.

        Returns
        -------
        list[str]
            Validation error messages.  Empty list means valid.
        """
        return []

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"

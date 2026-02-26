"""Plugin subsystem for agent-gov.

Provides decorator-based registration for custom rules and compliance
frameworks.  Third-party implementations register via this system using
``importlib.metadata`` entry-points under the ``"agent_gov.rules"`` and
``"agent_gov.frameworks"`` groups.

Example
-------
Register a custom rule::

    from agent_gov.plugins.registry import rule_registry
    from agent_gov.policy.rule import PolicyRule, RuleVerdict

    @rule_registry.register("my_custom_rule")
    class MyCustomRule(PolicyRule):
        name = "my_custom_rule"

        def evaluate(self, action, config):
            return RuleVerdict(rule_name=self.name, passed=True)

Register a custom framework::

    from agent_gov.plugins.registry import framework_registry
    from agent_gov.frameworks.base import ComplianceFramework

    @framework_registry.register("my-framework")
    class MyFramework(ComplianceFramework):
        name = "my-framework"
        ...
"""
from __future__ import annotations

from agent_gov.plugins.registry import (
    FrameworkRegistry,
    RuleRegistry,
    framework_registry,
    rule_registry,
)

__all__ = [
    "FrameworkRegistry",
    "RuleRegistry",
    "framework_registry",
    "rule_registry",
]

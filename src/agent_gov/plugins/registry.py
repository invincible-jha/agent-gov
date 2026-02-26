"""Rule and Framework registries for agent-gov.

Provides:

- :class:`RuleRegistry` — register custom :class:`~agent_gov.policy.rule.PolicyRule` subclasses
- :class:`FrameworkRegistry` — register custom
  :class:`~agent_gov.frameworks.base.ComplianceFramework` subclasses
- :data:`rule_registry` — global singleton rule registry
- :data:`framework_registry` — global singleton framework registry

Both registries pre-populate with the built-in implementations so they can
be queried for the full set of available rules/frameworks.

Plugin entry-points
-------------------
Third-party packages can register rules and frameworks by declaring
entry-points in their ``pyproject.toml``::

    [project.entry-points."agent_gov.rules"]
    my_rule = "my_package.rules:MyRule"

    [project.entry-points."agent_gov.frameworks"]
    my-framework = "my_package.frameworks:MyFramework"

Then call::

    rule_registry.load_entrypoints("agent_gov.rules")
    framework_registry.load_entrypoints("agent_gov.frameworks")
"""
from __future__ import annotations

import importlib.metadata
import logging
from collections.abc import Callable
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generic plugin registry (kept here to avoid re-exporting the ABC-bound one)
# ---------------------------------------------------------------------------

T = TypeVar("T")


class _GenericRegistry(Generic[T]):
    """Lightweight key → class registry without ABC enforcement."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._entries: dict[str, type[T]] = {}

    @property
    def registry_name(self) -> str:
        """Human-readable registry name."""
        return self._name

    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        """Decorator that registers a class under ``name``."""

        def decorator(cls: type[T]) -> type[T]:
            if name in self._entries:
                logger.warning(
                    "Overwriting existing registration %r in registry %r.",
                    name,
                    self._name,
                )
            self._entries[name] = cls
            logger.debug(
                "Registered %r -> %s in %r registry.",
                name,
                cls.__qualname__,  # type: ignore[attr-defined]
                self._name,
            )
            return cls

        return decorator

    def register_class(self, name: str, cls: type[T]) -> None:
        """Register a class directly without using the decorator."""
        self._entries[name] = cls

    def get(self, name: str) -> type[T]:
        """Return the class registered under ``name``.

        Raises
        ------
        KeyError
            If no class is registered under ``name``.
        """
        if name not in self._entries:
            raise KeyError(
                f"{name!r} is not registered in the {self._name!r} registry. "
                f"Available: {sorted(self._entries)!r}"
            )
        return self._entries[name]

    def list_names(self) -> list[str]:
        """Return sorted list of all registered names."""
        return sorted(self._entries)

    def __contains__(self, name: object) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"Registry(name={self._name!r}, entries={self.list_names()})"

    def load_entrypoints(self, group: str) -> None:
        """Load and register classes declared as package entry-points.

        Already-registered names are skipped (idempotent).

        Parameters
        ----------
        group:
            Entry-point group to scan.
        """
        for ep in importlib.metadata.entry_points(group=group):
            if ep.name in self._entries:
                logger.debug(
                    "Entry-point %r already registered in %r; skipping.",
                    ep.name,
                    self._name,
                )
                continue
            try:
                cls = ep.load()
                self.register_class(ep.name, cls)
                logger.debug("Loaded entry-point %r into %r registry.", ep.name, self._name)
            except Exception:
                logger.exception(
                    "Failed to load entry-point %r from group %r; skipping.",
                    ep.name,
                    group,
                )


# ---------------------------------------------------------------------------
# Typed aliases with docstrings
# ---------------------------------------------------------------------------

from agent_gov.policy.rule import PolicyRule  # noqa: E402
from agent_gov.frameworks.base import ComplianceFramework  # noqa: E402


class RuleRegistry(_GenericRegistry[PolicyRule]):
    """Registry for :class:`~agent_gov.policy.rule.PolicyRule` subclasses."""


class FrameworkRegistry(_GenericRegistry[ComplianceFramework]):
    """Registry for :class:`~agent_gov.frameworks.base.ComplianceFramework` subclasses."""


# ---------------------------------------------------------------------------
# Global singletons pre-populated with built-ins
# ---------------------------------------------------------------------------

rule_registry: RuleRegistry = RuleRegistry("rules")
framework_registry: FrameworkRegistry = FrameworkRegistry("frameworks")


def _populate_builtins() -> None:
    """Register all built-in rules and frameworks into the global singletons."""
    from agent_gov.rules.cost_limit import CostLimitRule
    from agent_gov.rules.keyword_block import KeywordBlockRule
    from agent_gov.rules.pii_check import PiiCheckRule
    from agent_gov.rules.role_check import RoleCheckRule

    for rule_cls in (PiiCheckRule, RoleCheckRule, CostLimitRule, KeywordBlockRule):
        rule_registry.register_class(rule_cls.name, rule_cls)

    from agent_gov.frameworks.eu_ai_act import EuAiActFramework
    from agent_gov.frameworks.gdpr import GdprFramework
    from agent_gov.frameworks.hipaa import HipaaFramework
    from agent_gov.frameworks.soc2 import Soc2Framework

    for fw_cls in (EuAiActFramework, GdprFramework, HipaaFramework, Soc2Framework):
        framework_registry.register_class(fw_cls.name, fw_cls)


_populate_builtins()

# Backward-compatible alias for code that imported PluginRegistry from the original scaffold.
PluginRegistry = _GenericRegistry

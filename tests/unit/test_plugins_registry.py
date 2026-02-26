"""Tests for agent_gov.plugins.registry — RuleRegistry, FrameworkRegistry, builtins."""
from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from agent_gov.plugins.registry import (
    FrameworkRegistry,
    RuleRegistry,
    _GenericRegistry,
    framework_registry,
    rule_registry,
)


class TestGenericRegistry:
    def test_register_decorator(self) -> None:
        from agent_gov.policy.rule import PolicyRule, RuleVerdict

        reg: _GenericRegistry[PolicyRule] = _GenericRegistry("test-rules")

        class _Dummy(PolicyRule):
            name = "dummy"

            def evaluate(self, action, config):  # type: ignore[override]
                return RuleVerdict(rule_name="dummy", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        reg.register("dummy")(_Dummy)
        assert reg.get("dummy") is _Dummy

    def test_register_overwrites_with_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        from agent_gov.policy.rule import PolicyRule, RuleVerdict

        reg: _GenericRegistry[PolicyRule] = _GenericRegistry("warn-test")

        class _A(PolicyRule):
            name = "a"

            def evaluate(self, action, config):
                return RuleVerdict(rule_name="a", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        class _B(PolicyRule):
            name = "b"

            def evaluate(self, action, config):
                return RuleVerdict(rule_name="b", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        reg.register_class("key", _A)
        with caplog.at_level(logging.WARNING):
            reg.register("key")(_B)
        assert reg.get("key") is _B

    def test_register_class_direct(self) -> None:
        from agent_gov.policy.rule import PolicyRule, RuleVerdict

        reg: _GenericRegistry[PolicyRule] = _GenericRegistry("direct")

        class _D(PolicyRule):
            name = "d"

            def evaluate(self, action, config):
                return RuleVerdict(rule_name="d", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        reg.register_class("d", _D)
        assert "d" in reg

    def test_get_missing_raises_key_error(self) -> None:
        reg: _GenericRegistry = _GenericRegistry("empty")
        with pytest.raises(KeyError, match="not registered"):
            reg.get("nonexistent")

    def test_list_names_sorted(self) -> None:
        from agent_gov.policy.rule import PolicyRule, RuleVerdict

        reg: _GenericRegistry[PolicyRule] = _GenericRegistry("sorted-test")

        class _Z(PolicyRule):
            name = "z"

            def evaluate(self, action, config):
                return RuleVerdict(rule_name="z", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        class _A(PolicyRule):
            name = "a"

            def evaluate(self, action, config):
                return RuleVerdict(rule_name="a", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        reg.register_class("z", _Z)
        reg.register_class("a", _A)
        assert reg.list_names() == ["a", "z"]

    def test_contains_operator(self) -> None:
        from agent_gov.policy.rule import PolicyRule, RuleVerdict

        reg: _GenericRegistry[PolicyRule] = _GenericRegistry("contains-test")
        assert "anything" not in reg

    def test_len_operator(self) -> None:
        reg: _GenericRegistry = _GenericRegistry("len-test")
        assert len(reg) == 0

    def test_repr_includes_name(self) -> None:
        reg: _GenericRegistry = _GenericRegistry("my-registry")
        assert "my-registry" in repr(reg)

    def test_load_entrypoints_skips_already_registered(self) -> None:
        reg: _GenericRegistry = _GenericRegistry("ep-test")
        mock_ep = MagicMock()
        mock_ep.name = "existing"

        from agent_gov.policy.rule import PolicyRule, RuleVerdict

        class _Existing(PolicyRule):
            name = "existing"

            def evaluate(self, action, config):
                return RuleVerdict(rule_name="existing", passed=True, severity="low", message="ok")

            def validate_config(self, config):
                return []

        reg.register_class("existing", _Existing)

        with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
            reg.load_entrypoints("some.group")

        # Should still be the original class
        assert reg.get("existing") is _Existing

    def test_load_entrypoints_handles_load_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        reg: _GenericRegistry = _GenericRegistry("ep-fail-test")
        mock_ep = MagicMock()
        mock_ep.name = "bad-plugin"
        mock_ep.load.side_effect = ImportError("no module")

        with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
            with caplog.at_level(logging.ERROR):
                reg.load_entrypoints("some.group")

        assert "bad-plugin" not in reg


class TestBuiltinRegistries:
    def test_rule_registry_has_pii_check(self) -> None:
        assert "pii_check" in rule_registry

    def test_rule_registry_has_role_check(self) -> None:
        assert "role_check" in rule_registry

    def test_rule_registry_has_cost_limit(self) -> None:
        assert "cost_limit" in rule_registry

    def test_rule_registry_has_keyword_block(self) -> None:
        assert "keyword_block" in rule_registry

    def test_framework_registry_has_gdpr(self) -> None:
        assert "gdpr" in framework_registry

    def test_framework_registry_has_hipaa(self) -> None:
        assert "hipaa" in framework_registry

    def test_framework_registry_has_soc2(self) -> None:
        assert "soc2" in framework_registry

    def test_framework_registry_has_eu_ai_act(self) -> None:
        assert "eu-ai-act" in framework_registry

    def test_rule_registry_list_names_sorted(self) -> None:
        names = rule_registry.list_names()
        assert names == sorted(names)

    def test_framework_registry_list_names_sorted(self) -> None:
        names = framework_registry.list_names()
        assert names == sorted(names)

    def test_rule_registry_get_instantiatable(self) -> None:
        cls = rule_registry.get("pii_check")
        instance = cls()
        assert hasattr(instance, "evaluate")

    def test_framework_registry_get_instantiatable(self) -> None:
        cls = framework_registry.get("gdpr")
        instance = cls()
        assert hasattr(instance, "run_check")

    def test_framework_registry_contains_operator(self) -> None:
        assert "gdpr" in framework_registry
        assert "nonexistent" not in framework_registry

"""Tests for agent_gov.integration.agentcore_bridge — AgentCoreBridge."""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_gov.integration.agentcore_bridge import AgentCoreBridge, _AGENTCORE_AVAILABLE
from agent_gov.policy.schema import PolicyConfig


def _make_policy(tmp_path: Path) -> "PolicyConfig":
    from agent_gov.policy.loader import PolicyLoader

    policy_yaml = tmp_path / "p.yaml"
    policy_yaml.write_text(
        "name: bridge-policy\nversion: '1.0'\nrules:\n  - name: pii-rule\n    type: pii_check\n    enabled: true\n    severity: high\n"
    )
    return PolicyLoader().load_file(str(policy_yaml))


class TestAgentCoreBridgeNoAgentcore:
    """Tests that apply when agentcore-sdk is NOT installed (the typical CI case)."""

    def test_is_available_reflects_install_status(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        # Whether True or False depends on environment; just confirm it's a bool.
        assert isinstance(bridge.is_available, bool)

    def test_is_connected_initially_false(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        assert bridge.is_connected is False

    def test_connect_returns_false_when_unavailable(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)

        with patch(
            "agent_gov.integration.agentcore_bridge._AGENTCORE_AVAILABLE", False
        ):
            result = bridge.connect()
        assert result is False

    def test_disconnect_noop_when_unavailable(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        # Should not raise even when agentcore not available
        with patch(
            "agent_gov.integration.agentcore_bridge._AGENTCORE_AVAILABLE", False
        ):
            bridge.disconnect()

    def test_evaluate_event_passes_clean_action(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        result = bridge.evaluate_event({"type": "search", "query": "hello"})
        assert isinstance(result, bool)

    def test_evaluate_event_logs_audit_entry(self, tmp_path: Path) -> None:
        from agent_gov.audit.logger import AuditLogger

        policy = _make_policy(tmp_path)
        log_file = tmp_path / "audit.jsonl"
        audit_logger = AuditLogger(log_file)
        bridge = AgentCoreBridge(policy=policy, audit_logger=audit_logger)
        bridge.evaluate_event({"type": "search"}, agent_id="test-agent")
        assert log_file.exists()
        assert log_file.stat().st_size > 0

    def test_evaluate_event_without_audit_logger(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy, audit_logger=None)
        # Should not raise
        result = bridge.evaluate_event({"type": "search"})
        assert isinstance(result, bool)

    def test_custom_agent_id_field(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy, agent_id_field="user_id")
        # Verify the field is stored
        assert bridge._agent_id_field == "user_id"


class TestAgentCoreBridgeHandleEvent:
    """Tests for _handle_event (the internal event handler)."""

    def test_handle_event_logs_pass(self, tmp_path: Path) -> None:
        from agent_gov.audit.logger import AuditLogger

        policy = _make_policy(tmp_path)
        log_file = tmp_path / "audit.jsonl"
        audit_logger = AuditLogger(log_file)
        bridge = AgentCoreBridge(policy=policy, audit_logger=audit_logger)
        # Call _handle_event directly
        bridge._handle_event({"type": "search", "query": "safe content", "agent_id": "bot"})
        assert log_file.exists()

    def test_handle_event_logs_violation(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from agent_gov.audit.logger import AuditLogger
        from agent_gov.policy.loader import PolicyLoader

        policy_yaml = tmp_path / "strict.yaml"
        policy_yaml.write_text(
            "name: strict\nversion: '1.0'\nrules:\n"
            "  - name: kw-rule\n    type: keyword_block\n    enabled: true\n    severity: critical\n"
            "    params:\n      keywords:\n        - forbidden\n"
        )
        policy = PolicyLoader().load_file(str(policy_yaml))
        log_file = tmp_path / "audit.jsonl"
        audit_logger = AuditLogger(log_file)
        bridge = AgentCoreBridge(policy=policy, audit_logger=audit_logger)

        with caplog.at_level(logging.WARNING):
            bridge._handle_event({"type": "write", "content": "forbidden phrase", "agent_id": "bot"})

        assert log_file.exists()

    def test_handle_event_exception_does_not_propagate(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        # Pass a non-dict event to trigger internal exception handling
        bridge._handle_event("not-a-dict")  # type: ignore[arg-type]


class TestAgentCoreBridgeWithMockedAgentcore:
    """Tests that simulate agentcore-sdk being available via mocking."""

    def test_connect_subscribes_to_event_bus(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)

        mock_bus = MagicMock()
        mock_agentcore = MagicMock()
        mock_agentcore.get_event_bus.return_value = mock_bus

        with (
            patch("agent_gov.integration.agentcore_bridge._AGENTCORE_AVAILABLE", True),
            patch("agent_gov.integration.agentcore_bridge.agentcore", mock_agentcore),
        ):
            result = bridge.connect()

        assert result is True
        assert bridge.is_connected is True
        mock_bus.subscribe.assert_called_once_with("agent.action", bridge._handle_event)

    def test_connect_returns_false_on_exception(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)

        mock_agentcore = MagicMock()
        mock_agentcore.get_event_bus.side_effect = RuntimeError("bus error")

        with (
            patch("agent_gov.integration.agentcore_bridge._AGENTCORE_AVAILABLE", True),
            patch("agent_gov.integration.agentcore_bridge.agentcore", mock_agentcore),
        ):
            result = bridge.connect()

        assert result is False
        assert bridge.is_connected is False

    def test_disconnect_unsubscribes(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        bridge._connected = True  # Simulate connected state

        mock_bus = MagicMock()
        mock_agentcore = MagicMock()
        mock_agentcore.get_event_bus.return_value = mock_bus

        with (
            patch("agent_gov.integration.agentcore_bridge._AGENTCORE_AVAILABLE", True),
            patch("agent_gov.integration.agentcore_bridge.agentcore", mock_agentcore),
        ):
            bridge.disconnect()

        assert bridge.is_connected is False
        mock_bus.unsubscribe.assert_called_once()

    def test_disconnect_handles_exception_gracefully(self, tmp_path: Path) -> None:
        policy = _make_policy(tmp_path)
        bridge = AgentCoreBridge(policy=policy)
        bridge._connected = True

        mock_agentcore = MagicMock()
        mock_agentcore.get_event_bus.side_effect = RuntimeError("bus down")

        with (
            patch("agent_gov.integration.agentcore_bridge._AGENTCORE_AVAILABLE", True),
            patch("agent_gov.integration.agentcore_bridge.agentcore", mock_agentcore),
        ):
            # Should not raise
            bridge.disconnect()

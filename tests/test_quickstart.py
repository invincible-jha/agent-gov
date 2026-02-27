"""Test that the 3-line quickstart API works for agent-gov."""
from __future__ import annotations


def test_quickstart_import() -> None:
    from agent_gov import GovernanceEngine

    engine = GovernanceEngine()
    assert engine is not None


def test_quickstart_evaluate() -> None:
    from agent_gov import GovernanceEngine

    engine = GovernanceEngine()
    result = engine.evaluate({"action": "file_read", "path": "/data.csv"})
    assert result is not None


def test_quickstart_default_policy_passes() -> None:
    from agent_gov import GovernanceEngine

    engine = GovernanceEngine()
    result = engine.evaluate({"action": "search", "query": "Python AI"})
    assert result.passed is True


def test_quickstart_policy_property() -> None:
    from agent_gov import GovernanceEngine

    engine = GovernanceEngine()
    assert engine.policy is not None
    assert engine.policy.name == "quickstart-default"


def test_quickstart_repr() -> None:
    from agent_gov import GovernanceEngine

    engine = GovernanceEngine()
    text = repr(engine)
    assert "GovernanceEngine" in text
    assert "quickstart-default" in text

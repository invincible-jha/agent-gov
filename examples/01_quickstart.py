"""Quickstart example for agent-gov.

Run this script after installing the package::

    pip install agent-gov
    python examples/01_quickstart.py

This script demonstrates the end-to-end workflow:
1. Load a policy from a YAML pack
2. Evaluate actions against the policy
3. Run compliance framework checks
4. Log events to the audit trail
5. Generate a governance report
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import agent_gov
from agent_gov import (
    AuditLogger,
    AuditReader,
    EuAiActFramework,
    GdprFramework,
    PolicyEvaluator,
    PolicyLoader,
    ReportGenerator,
)


def demo_policy_evaluation() -> None:
    """Demonstrate loading a policy and evaluating actions."""
    print("\n=== Policy Evaluation ===\n")

    # Load the standard policy pack bundled with agent-gov
    packs_dir = Path(agent_gov.__file__).parent / "packs"
    loader = PolicyLoader()
    policy = loader.load_file(packs_dir / "standard.yaml")
    print(f"Loaded policy: {policy.name!r} (v{policy.version})")
    print(f"Rules: {[r.name for r in policy.rules]}")

    evaluator = PolicyEvaluator()

    # Action 1: a plain search — should pass
    safe_action: dict[str, object] = {
        "type": "search",
        "query": "quarterly revenue trends",
        "agent_role": "operator",
        "cost": 0.02,
    }
    report1 = evaluator.evaluate(policy, safe_action)
    print(f"\nSafe action: {report1.summary()}")

    # Action 2: action with a blocked keyword — should fail
    risky_action: dict[str, object] = {
        "type": "database_query",
        "query": "drop table users",
        "agent_role": "operator",
        "cost": 0.01,
    }
    report2 = evaluator.evaluate(policy, risky_action)
    print(f"Risky action: {report2.summary()}")
    for verdict in report2.failed_verdicts:
        print(f"  FAIL [{verdict.severity}] {verdict.rule_name}: {verdict.message}")

    # Action 3: action exceeding cost limit — should fail
    expensive_action: dict[str, object] = {
        "type": "llm_call",
        "prompt": "Write a detailed business plan",
        "agent_role": "operator",
        "cost": 1.50,
    }
    report3 = evaluator.evaluate(policy, expensive_action)
    print(f"Expensive action: {report3.summary()}")


def demo_compliance_frameworks() -> None:
    """Demonstrate running compliance framework checks."""
    print("\n=== Compliance Frameworks ===\n")

    # EU AI Act check with partial evidence
    eu_framework = EuAiActFramework()
    eu_evidence: dict[str, object] = {
        "A6": {"status": "pass", "evidence": "System classified as limited risk."},
        "A9": {"status": "pass", "evidence": "Risk management plan documented in confluence."},
        "A10": {"status": "fail", "evidence": "Training data audit not yet completed."},
        "A13": {"status": "pass", "evidence": "Model card published; outputs include confidence scores."},
        "A14": {"status": "pass", "evidence": "Human review required for all critical decisions."},
        "A15": {"status": "unknown"},
        "A52": {"status": "pass", "evidence": "UI displays 'AI-generated' badge on all responses."},
        "A60": {"status": "unknown", "evidence": "Awaiting EU database portal access."},
    }
    eu_report = eu_framework.run_check(eu_evidence)
    print(f"EU AI Act score: {eu_report.score_percent:.1f}%")
    print(f"  Passed: {eu_report.passed_count}  Failed: {eu_report.failed_count}  Unknown: {eu_report.unknown_count}")

    # GDPR check
    gdpr_framework = GdprFramework()
    gdpr_evidence: dict[str, object] = {
        "P1": {"status": "pass", "evidence": "Legitimate interest documented in ROPA."},
        "P2": {"status": "pass", "evidence": "Purpose documented and enforced."},
        "P3": {"status": "pass", "evidence": "Only email and name collected."},
        "P4": {"status": "unknown"},
        "P5": {"status": "pass", "evidence": "Auto-deletion after 90 days configured."},
        "P6": {"status": "pass", "evidence": "AES-256 at rest, TLS 1.3 in transit."},
        "P7": {"status": "fail", "evidence": "DPA not yet signed for EU operations."},
    }
    gdpr_report = gdpr_framework.run_check(gdpr_evidence)
    print(f"\nGDPR score: {gdpr_report.score_percent:.1f}%")


def demo_audit_logging() -> None:
    """Demonstrate audit log write and read."""
    print("\n=== Audit Logging ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"
        audit_logger = AuditLogger(log_path)

        # Load and evaluate some actions
        packs_dir = Path(agent_gov.__file__).parent / "packs"
        loader = PolicyLoader()
        policy = loader.load_file(packs_dir / "minimal.yaml")
        evaluator = PolicyEvaluator()

        actions: list[dict[str, object]] = [
            {"type": "search", "query": "product roadmap", "agent_id": "agent-alpha"},
            {"type": "file_read", "path": "/data/config.json", "agent_id": "agent-beta"},
            {"type": "api_call", "endpoint": "/api/users", "agent_id": "agent-alpha"},
        ]

        for action in actions:
            report = evaluator.evaluate(policy, action)
            audit_logger.log_from_report(
                report,
                agent_id=str(action.get("agent_id", "unknown")),
            )

        # Read back
        reader = AuditReader(log_path)
        stats = reader.stats()
        print(f"Logged {stats['total']} entries")
        print(f"  Pass: {stats['pass_count']}  Fail: {stats['fail_count']}")
        print(f"  Agents: {stats['agents']}")

        # Query a specific agent
        alpha_entries = reader.query(agent_id="agent-alpha")
        print(f"\nagent-alpha has {len(alpha_entries)} entries")


def main() -> None:
    print(f"agent-gov v{agent_gov.__version__}")
    print("=" * 50)

    demo_policy_evaluation()
    demo_compliance_frameworks()
    demo_audit_logging()

    print("\nQuickstart complete.")


if __name__ == "__main__":
    main()

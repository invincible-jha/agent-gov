#!/usr/bin/env python3
"""Example: Audit Log Search

Demonstrates writing audit entries and then searching, filtering,
and aggregating them with the audit subsystem.

Usage:
    python examples/04_audit_search.py

Requirements:
    pip install agent-gov
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import agent_gov
from agent_gov import (
    AuditEntry,
    AuditLogger,
    AuditReader,
    RuleVerdict,
    Severity,
    search_entries,
    aggregate_verdicts,
    aggregate_by_agent,
    aggregate_by_action_type,
    build_filter,
)


def populate_audit_log(audit_logger: AuditLogger) -> None:
    """Write sample audit entries."""
    sample_entries: list[dict[str, object]] = [
        {"agent_id": "agent-alpha", "action_type": "search", "verdict": "pass", "policy": "standard-v1"},
        {"agent_id": "agent-alpha", "action_type": "file_read", "verdict": "pass", "policy": "standard-v1"},
        {"agent_id": "agent-beta", "action_type": "delete", "verdict": "fail", "policy": "standard-v1"},
        {"agent_id": "agent-beta", "action_type": "search", "verdict": "pass", "policy": "standard-v1"},
        {"agent_id": "agent-gamma", "action_type": "llm_call", "verdict": "fail", "policy": "cost-policy"},
        {"agent_id": "agent-gamma", "action_type": "api_call", "verdict": "pass", "policy": "standard-v1"},
        {"agent_id": "agent-alpha", "action_type": "delete", "verdict": "pass", "policy": "standard-v1"},
    ]

    for entry_data in sample_entries:
        entry = AuditEntry(
            agent_id=str(entry_data["agent_id"]),
            action_type=str(entry_data["action_type"]),
            verdict=str(entry_data["verdict"]),
            policy_name=str(entry_data["policy"]),
            severity=Severity.LOW if entry_data["verdict"] == "pass" else Severity.HIGH,
        )
        audit_logger.log(entry)


def main() -> None:
    print(f"agent-gov version: {agent_gov.__version__}")

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"
        audit_logger = AuditLogger(log_path)

        # Step 1: Populate audit log
        populate_audit_log(audit_logger)
        reader = AuditReader(log_path)
        all_entries = reader.all()
        print(f"Total audit entries: {len(all_entries)}")

        # Step 2: Search by agent
        alpha_filter = build_filter(agent_id="agent-alpha")
        alpha_entries = search_entries(all_entries, filters=[alpha_filter])
        print(f"\nagent-alpha entries: {len(alpha_entries)}")

        # Step 3: Search for failures
        fail_filter = build_filter(verdict="fail")
        failures = search_entries(all_entries, filters=[fail_filter])
        print(f"Failed entries: {len(failures)}")
        for entry in failures:
            print(f"  [{entry.agent_id}] {entry.action_type} -> {entry.verdict}")

        # Step 4: Aggregate by agent
        by_agent = aggregate_by_agent(all_entries)
        print(f"\nEntries per agent:")
        for agent_id, count in by_agent.items():
            print(f"  {agent_id}: {count}")

        # Step 5: Aggregate by action type
        by_action = aggregate_by_action_type(all_entries)
        print(f"\nEntries per action type:")
        for action_type, count in by_action.items():
            print(f"  {action_type}: {count}")

        # Step 6: Verdict summary
        verdict_summary = aggregate_verdicts(all_entries)
        print(f"\nVerdict summary:")
        print(f"  pass={verdict_summary.get('pass', 0)} fail={verdict_summary.get('fail', 0)}")


if __name__ == "__main__":
    main()

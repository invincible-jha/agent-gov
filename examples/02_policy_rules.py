#!/usr/bin/env python3
"""Example: Custom Policy Rules

Demonstrates building a custom policy with built-in rules (keyword
block, PII check, cost limit, role check) and evaluating actions.

Usage:
    python examples/02_policy_rules.py

Requirements:
    pip install agent-gov
"""
from __future__ import annotations

import agent_gov
from agent_gov import (
    PolicyEvaluator,
    PolicyConfig,
    RuleConfig,
    Severity,
    KeywordBlockRule,
    PiiCheckRule,
    CostLimitRule,
    RoleCheckRule,
)


def build_policy_config() -> PolicyConfig:
    """Build a custom policy with multiple rules."""
    return PolicyConfig(
        name="enterprise-policy-v1",
        version="1.0",
        rules=[
            RuleConfig(
                rule_class="keyword_block",
                name="block-dangerous-sql",
                parameters={"keywords": ["drop table", "delete from", "truncate"]},
                severity=Severity.CRITICAL,
            ),
            RuleConfig(
                rule_class="pii_check",
                name="no-pii-in-prompts",
                parameters={"patterns": ["ssn", "credit_card", "phone"]},
                severity=Severity.HIGH,
            ),
            RuleConfig(
                rule_class="cost_limit",
                name="daily-cost-cap",
                parameters={"max_cost_usd": 1.0},
                severity=Severity.MEDIUM,
            ),
            RuleConfig(
                rule_class="role_check",
                name="operator-only-delete",
                parameters={"allowed_roles": ["admin", "operator"], "action_type": "delete"},
                severity=Severity.HIGH,
            ),
        ],
    )


def main() -> None:
    print(f"agent-gov version: {agent_gov.__version__}")

    # Step 1: Build policy from config
    config = build_policy_config()
    print(f"Policy '{config.name}' with {len(config.rules)} rules.")

    # Step 2: Create evaluator
    evaluator = PolicyEvaluator()

    # Step 3: Test various actions
    test_actions: list[tuple[str, dict[str, object]]] = [
        ("Safe search", {"type": "search", "query": "Q4 results", "agent_role": "viewer", "cost": 0.01}),
        ("SQL injection attempt", {"type": "database_query", "query": "drop table users", "agent_role": "operator", "cost": 0.01}),
        ("High-cost call", {"type": "llm_call", "prompt": "Generate report", "agent_role": "operator", "cost": 2.50}),
        ("Unauthorised delete", {"type": "delete", "target": "log_files", "agent_role": "viewer", "cost": 0.001}),
        ("Admin delete", {"type": "delete", "target": "old_data", "agent_role": "admin", "cost": 0.001}),
    ]

    print("\nPolicy evaluation results:")
    for label, action in test_actions:
        try:
            report = evaluator.evaluate_from_config(config, action)
            status = "PASS" if report.passed else "FAIL"
            print(f"  [{status}] {label}")
            if not report.passed:
                for verdict in report.failed_verdicts:
                    print(f"         -> {verdict.rule_name}: {verdict.message[:60]}")
        except Exception as error:
            print(f"  [ERROR] {label}: {error}")


if __name__ == "__main__":
    main()

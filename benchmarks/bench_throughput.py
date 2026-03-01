"""Benchmark: PolicyEvaluator throughput — evaluations per second.

Measures how many policy evaluations can be completed per second using
the built-in rule set (pii_check, role_check, cost_limit, keyword_block).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity

_ITERATIONS: int = 10_000


def _make_policy() -> PolicyConfig:
    """Build a minimal policy with four built-in rules."""
    return PolicyConfig(
        name="bench-policy",
        version="1.0",
        description="Benchmark policy",
        rules=[
            RuleConfig(
                name="no-pii",
                type="pii_check",
                severity=Severity.HIGH,
                params={"check_email": True, "check_ssn": False},
            ),
            RuleConfig(
                name="role-gate",
                type="role_check",
                severity=Severity.MEDIUM,
                params={"allowed_roles": ["admin", "agent"]},
            ),
            RuleConfig(
                name="cost-cap",
                type="cost_limit",
                severity=Severity.MEDIUM,
                params={"max_cost_usd": 1.0},
            ),
            RuleConfig(
                name="no-bad-words",
                type="keyword_block",
                severity=Severity.LOW,
                params={"keywords": ["badword"]},
            ),
        ],
    )


def bench_policy_evaluation_throughput() -> dict[str, object]:
    """Benchmark PolicyEvaluator.evaluate() throughput.

    Returns
    -------
    dict with keys: operation, iterations, total_seconds, ops_per_second,
    avg_latency_ms.
    """
    evaluator = PolicyEvaluator(strict=False)
    policy = _make_policy()
    action: dict[str, object] = {
        "type": "search",
        "query": "list all users",
        "role": "agent",
        "estimated_cost_usd": 0.01,
    }

    start = time.perf_counter()
    for _ in range(_ITERATIONS):
        evaluator.evaluate(policy, action)
    total = time.perf_counter() - start

    result: dict[str, object] = {
        "operation": "policy_evaluation_throughput",
        "iterations": _ITERATIONS,
        "total_seconds": round(total, 4),
        "ops_per_second": round(_ITERATIONS / total, 1),
        "avg_latency_ms": round(total / _ITERATIONS * 1000, 4),
    }
    print(
        f"[bench_throughput] {result['operation']}: "
        f"{result['ops_per_second']:,.0f} ops/sec  "
        f"avg {result['avg_latency_ms']:.4f} ms"
    )
    return result


if __name__ == "__main__":
    result = bench_policy_evaluation_throughput()
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "throughput_baseline.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(f"Results saved to {output_path}")

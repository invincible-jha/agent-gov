"""Benchmark: Compliance framework check latency (p50/p95/mean).

Measures the per-call latency of a single policy evaluation with each
built-in rule individually enabled, capturing the p50, p95, and mean
latency distributions.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity

_WARMUP: int = 100
_ITERATIONS: int = 5_000


def _make_single_rule_policy(rule_type: str) -> PolicyConfig:
    """Create a policy with exactly one enabled rule."""
    return PolicyConfig(
        name=f"bench-{rule_type}",
        version="1.0",
        description=f"Single-rule policy for {rule_type}",
        rules=[
            RuleConfig(
                name=rule_type,
                type=rule_type,
                severity=Severity.MEDIUM,
                params={},
            )
        ],
    )


def bench_compliance_check_latency() -> dict[str, object]:
    """Benchmark single compliance rule check latency.

    Returns
    -------
    dict with keys: operation, iterations, total_seconds, ops_per_second,
    avg_latency_ms, p50_ms, p95_ms.
    """
    evaluator = PolicyEvaluator(strict=False)
    policy = _make_single_rule_policy("cost_limit")
    action: dict[str, object] = {
        "estimated_cost_usd": 0.50,
        "role": "agent",
    }

    # Warmup
    for _ in range(_WARMUP):
        evaluator.evaluate(policy, action)

    latencies_ms: list[float] = []
    for _ in range(_ITERATIONS):
        t0 = time.perf_counter()
        evaluator.evaluate(policy, action)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)
    total = sum(latencies_ms) / 1000

    result: dict[str, object] = {
        "operation": "compliance_check_latency",
        "iterations": _ITERATIONS,
        "total_seconds": round(total, 4),
        "ops_per_second": round(_ITERATIONS / total, 1),
        "avg_latency_ms": round(sum(latencies_ms) / n, 4),
        "p50_ms": round(sorted_lats[int(n * 0.50)], 4),
        "p95_ms": round(sorted_lats[min(int(n * 0.95), n - 1)], 4),
    }
    print(
        f"[bench_latency] {result['operation']}: "
        f"p50={result['p50_ms']:.4f}ms  p95={result['p95_ms']:.4f}ms  "
        f"mean={result['avg_latency_ms']:.4f}ms"
    )
    return result


if __name__ == "__main__":
    result = bench_compliance_check_latency()
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "latency_baseline.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(f"Results saved to {output_path}")

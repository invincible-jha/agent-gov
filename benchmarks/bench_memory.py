"""Benchmark: Memory usage of PolicyEvaluator and policy evaluation.

Uses tracemalloc to measure peak memory allocated during policy
construction and repeated evaluation.
"""
from __future__ import annotations

import json
import sys
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity

_ITERATIONS: int = 1_000


def bench_policy_evaluation_memory() -> dict[str, object]:
    """Benchmark memory usage during policy evaluation.

    Returns
    -------
    dict with keys: operation, iterations, peak_memory_kb, current_memory_kb.
    """
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    evaluator = PolicyEvaluator(strict=False)
    policy = PolicyConfig(
        name="bench-memory-policy",
        version="1.0",
        description="Memory benchmark policy",
        rules=[
            RuleConfig(
                name="cost-cap",
                type="cost_limit",
                severity=Severity.MEDIUM,
                params={"max_cost_usd": 1.0},
            ),
        ],
    )
    action: dict[str, object] = {"estimated_cost_usd": 0.10, "role": "agent"}

    for _ in range(_ITERATIONS):
        evaluator.evaluate(policy, action)

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_bytes = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
    peak_kb = round(total_bytes / 1024, 2)

    result: dict[str, object] = {
        "operation": "policy_evaluation_memory",
        "iterations": _ITERATIONS,
        "peak_memory_kb": peak_kb,
        "current_memory_kb": peak_kb,
        "ops_per_second": 0.0,
        "avg_latency_ms": 0.0,
    }
    print(f"[bench_memory] {result['operation']}: peak {peak_kb:.2f} KB over {_ITERATIONS} iterations")
    return result


if __name__ == "__main__":
    result = bench_policy_evaluation_memory()
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "memory_baseline.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(f"Results saved to {output_path}")

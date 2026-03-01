"""Structural tests for agent-gov benchmark module.

Verifies that benchmark functions are importable and return the expected
result dict keys. These are fast smoke tests, not full performance runs.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))


def test_bench_throughput_importable() -> None:
    """Verify bench_throughput module can be imported."""
    mod = importlib.import_module("bench_throughput")
    assert hasattr(mod, "bench_policy_evaluation_throughput")


def test_bench_latency_importable() -> None:
    """Verify bench_latency module can be imported."""
    mod = importlib.import_module("bench_latency")
    assert hasattr(mod, "bench_compliance_check_latency")


def test_bench_memory_importable() -> None:
    """Verify bench_memory module can be imported."""
    mod = importlib.import_module("bench_memory")
    assert hasattr(mod, "bench_policy_evaluation_memory")


def test_throughput_returns_expected_keys() -> None:
    """Verify bench_policy_evaluation_throughput returns expected result keys."""
    from bench_throughput import bench_policy_evaluation_throughput

    result = bench_policy_evaluation_throughput()
    assert "operation" in result
    assert "iterations" in result
    assert "total_seconds" in result
    assert "ops_per_second" in result
    assert "avg_latency_ms" in result
    assert float(result["ops_per_second"]) > 0  # type: ignore[arg-type]


def test_latency_returns_expected_keys() -> None:
    """Verify bench_compliance_check_latency returns expected result keys."""
    from bench_latency import bench_compliance_check_latency

    result = bench_compliance_check_latency()
    assert "operation" in result
    assert "ops_per_second" in result
    assert "avg_latency_ms" in result
    assert "p50_ms" in result
    assert "p95_ms" in result


def test_memory_returns_expected_keys() -> None:
    """Verify bench_policy_evaluation_memory returns expected result keys."""
    from bench_memory import bench_policy_evaluation_memory

    result = bench_policy_evaluation_memory()
    assert "operation" in result
    assert "peak_memory_kb" in result

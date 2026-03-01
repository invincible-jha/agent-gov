#!/usr/bin/env python3
"""Example: Compliance Frameworks

Demonstrates running EU AI Act, GDPR, HIPAA, and SOC 2 compliance
checks and generating a consolidated report.

Usage:
    python examples/03_compliance_frameworks.py

Requirements:
    pip install agent-gov
"""
from __future__ import annotations

import agent_gov
from agent_gov import (
    EuAiActFramework,
    GdprFramework,
    HipaaFramework,
    Soc2Framework,
    FrameworkReport,
)


FULL_PASS_EVIDENCE: dict[str, object] = {
    check_id: {"status": "pass", "evidence": "Control implemented and verified."}
    for check_id in ["A6", "A9", "A10", "A13", "A14", "A15", "A52", "A60",
                     "P1", "P2", "P3", "P4", "P5", "P6", "P7",
                     "H1", "H2", "H3", "H4", "H5",
                     "S1", "S2", "S3", "S4", "S5", "S6"]
}

PARTIAL_EVIDENCE: dict[str, object] = {
    "A6": {"status": "pass", "evidence": "System classified as limited risk."},
    "A9": {"status": "pass", "evidence": "Risk management plan documented."},
    "A10": {"status": "fail", "evidence": "Training data audit incomplete."},
    "A13": {"status": "pass", "evidence": "Model card published."},
    "A14": {"status": "unknown"},
    "P1": {"status": "pass", "evidence": "Legal basis documented."},
    "P2": {"status": "pass", "evidence": "Purpose limitation enforced."},
    "P3": {"status": "fail", "evidence": "Data minimisation review pending."},
    "H1": {"status": "pass", "evidence": "PHI access controls in place."},
    "H2": {"status": "unknown"},
    "S1": {"status": "pass", "evidence": "Security policy documented."},
    "S2": {"status": "pass", "evidence": "Incident response plan active."},
}


def run_framework(name: str, framework: object, evidence: dict[str, object]) -> FrameworkReport:
    """Run a compliance framework check and print results."""
    report: FrameworkReport = framework.run_check(evidence)  # type: ignore[attr-defined]
    status = "PASS" if report.score_percent >= 70.0 else "FAIL"
    print(f"  [{status}] {name}: {report.score_percent:.1f}% "
          f"(P={report.passed_count} F={report.failed_count} U={report.unknown_count})")
    return report


def main() -> None:
    print(f"agent-gov version: {agent_gov.__version__}")

    # Step 1: Run all four compliance frameworks
    print("\nCompliance framework checks (partial evidence):")
    frameworks: list[tuple[str, object]] = [
        ("EU AI Act", EuAiActFramework()),
        ("GDPR", GdprFramework()),
        ("HIPAA", HipaaFramework()),
        ("SOC 2", Soc2Framework()),
    ]

    reports: list[tuple[str, FrameworkReport]] = []
    for framework_name, framework in frameworks:
        report = run_framework(framework_name, framework, PARTIAL_EVIDENCE)
        reports.append((framework_name, report))

    # Step 2: Consolidated summary
    total_passed = sum(r.passed_count for _, r in reports)
    total_failed = sum(r.failed_count for _, r in reports)
    total_unknown = sum(r.unknown_count for _, r in reports)
    average_score = sum(r.score_percent for _, r in reports) / len(reports)

    print(f"\nConsolidated summary:")
    print(f"  Average score: {average_score:.1f}%")
    print(f"  Total passed: {total_passed} | failed: {total_failed} | unknown: {total_unknown}")

    # Step 3: Show failed items
    print("\nFailed checks:")
    for framework_name, report in reports:
        for item in report.items:
            if item.status == "fail":
                print(f"  [{framework_name}] {item.check_id}: {item.evidence[:60] if item.evidence else 'No evidence'}")


if __name__ == "__main__":
    main()

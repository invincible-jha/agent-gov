#!/usr/bin/env python3
"""Example: Governance Reporting

Demonstrates generating JSON and Markdown governance reports from
policy evaluation results.

Usage:
    python examples/05_reporting.py

Requirements:
    pip install agent-gov
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import agent_gov
from agent_gov import (
    GovernanceEngine,
    JsonReporter,
    MarkdownReporter,
    ReportGenerator,
    list_templates,
    get_template,
)


def main() -> None:
    print(f"agent-gov version: {agent_gov.__version__}")

    # Step 1: Use GovernanceEngine convenience class
    engine = GovernanceEngine()
    print("GovernanceEngine ready.")

    # Step 2: Evaluate several actions
    actions: list[dict[str, object]] = [
        {"type": "search", "query": "revenue report", "agent_role": "operator", "cost": 0.01},
        {"type": "database_query", "query": "drop table logs", "agent_role": "operator", "cost": 0.01},
        {"type": "llm_call", "prompt": "Draft email", "agent_role": "operator", "cost": 0.50},
    ]

    evaluation_results = []
    for action in actions:
        try:
            result = engine.evaluate(action)
            evaluation_results.append(result)
        except Exception as error:
            print(f"  Evaluation error for {action.get('type')}: {error}")

    print(f"Evaluated {len(evaluation_results)} actions.")

    # Step 3: Generate a JSON report
    json_reporter = JsonReporter()
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "governance_report.json"
        json_reporter.write(evaluation_results, output_path=json_path)
        report_data = json.loads(json_path.read_text())
        print(f"\nJSON report: {len(report_data.get('results', []))} results")

        # Step 4: Generate a Markdown report
        md_reporter = MarkdownReporter()
        md_path = Path(tmpdir) / "governance_report.md"
        md_reporter.write(evaluation_results, output_path=md_path)
        md_content = md_path.read_text()
        print(f"Markdown report: {len(md_content)} chars")
        print(f"  Preview: {md_content[:100].strip()}...")

    # Step 5: List available report templates
    templates = list_templates()
    print(f"\nAvailable templates ({len(templates)}):")
    for template_name in templates[:3]:
        print(f"  - {template_name}")


if __name__ == "__main__":
    main()

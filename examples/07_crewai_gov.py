#!/usr/bin/env python3
"""Example: CrewAI Governance Integration

Demonstrates enforcing governance policies on CrewAI agent tasks
using a GovernanceEngine gate before task execution.

Usage:
    python examples/07_crewai_gov.py

Requirements:
    pip install agent-gov crewai
"""
from __future__ import annotations

try:
    from crewai import Agent, Task, Crew, Process
    _CREWAI_AVAILABLE = True
except ImportError:
    _CREWAI_AVAILABLE = False

import agent_gov
from agent_gov import GovernanceEngine, AuditLogger, StdoutStorage, AuditFormatter


def governed_task_runner(
    task_description: str,
    agent_role: str,
    engine: GovernanceEngine,
    audit_logger: AuditLogger,
) -> str:
    """Run a task through the governance gate before execution."""
    action = {
        "type": "task_execution",
        "description": task_description,
        "agent_role": agent_role,
        "cost": 0.05,
    }
    result = engine.evaluate(action)
    entry = AuditLogger.build_entry(
        agent_id=agent_role,
        action_type="task_execution",
        verdict="pass" if result.passed else "fail",
        policy_name="governance-v1",
    )
    audit_logger.log(entry)

    if not result.passed:
        return f"[BLOCKED] Task rejected by governance: {result.failed_verdicts[0].message[:60]}"
    return f"[APPROVED] Task '{task_description[:50]}' cleared for execution."


def main() -> None:
    print(f"agent-gov version: {agent_gov.__version__}")

    if not _CREWAI_AVAILABLE:
        print("crewai not installed — demonstrating governance gate only.")
        print("Install with: pip install crewai")

    # Step 1: Set up governance engine + audit logger
    engine = GovernanceEngine()
    storage = StdoutStorage()
    formatter = AuditFormatter()
    audit_logger = AuditLogger(storage=storage, formatter=formatter)

    # Step 2: Define tasks with different risk levels
    tasks: list[tuple[str, str]] = [
        ("Analyse Q4 sales data and produce a summary report", "operator"),
        ("Drop all user data tables to free up disk space", "operator"),
        ("Generate marketing copy for the new product launch", "operator"),
        ("Delete archived log files older than 90 days", "admin"),
        ("Search for competitor pricing information online", "viewer"),
    ]

    print("\nGovernance-gated task execution:")
    approved = 0
    blocked = 0
    for description, role in tasks:
        result = governed_task_runner(description, role, engine, audit_logger)
        print(f"  {result}")
        if result.startswith("[APPROVED]"):
            approved += 1
        else:
            blocked += 1

    # Step 3: If crewai available, run an approved crew
    if _CREWAI_AVAILABLE:
        print("\nRunning approved CrewAI crew:")
        analyst = Agent(
            role="Data Analyst",
            goal="Produce accurate data summaries",
            backstory="Expert data analyst.",
            verbose=False,
        )
        task = Task(
            description="Summarise Q4 performance metrics.",
            agent=analyst,
            expected_output="A concise Q4 performance summary.",
        )
        crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=False)
        crew_result = crew.kickoff()
        print(f"  Crew output: {str(crew_result)[:80]}")

    print(f"\nGovernance summary: {approved} approved, {blocked} blocked")


if __name__ == "__main__":
    main()

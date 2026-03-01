#!/usr/bin/env python3
"""Example: LangChain Governance Integration

Demonstrates wrapping LangChain tool calls with an agent-gov policy
gate so non-compliant actions are blocked before execution.

Usage:
    python examples/06_langchain_gov.py

Requirements:
    pip install agent-gov langchain
"""
from __future__ import annotations

try:
    from langchain.tools import BaseTool
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False

import agent_gov
from agent_gov import GovernanceEngine, Severity


class GovernedToolWrapper:
    """Wraps any callable with a governance policy gate."""

    def __init__(self, tool_name: str, engine: GovernanceEngine) -> None:
        self._tool_name = tool_name
        self._engine = engine
        self._blocked_count = 0
        self._allowed_count = 0

    def run(self, arguments: dict[str, object]) -> str:
        action = {
            "type": self._tool_name,
            "agent_role": str(arguments.get("agent_role", "operator")),
            "cost": float(arguments.get("estimated_cost", 0.01)),
            **arguments,
        }
        try:
            result = self._engine.evaluate(action)
            if result.passed:
                self._allowed_count += 1
                return f"[{self._tool_name}] executed: {list(arguments.keys())}"
            else:
                self._blocked_count += 1
                failed = "; ".join(v.message for v in result.failed_verdicts)
                return f"[BLOCKED] {self._tool_name}: {failed[:80]}"
        except Exception as error:
            return f"[ERROR] {self._tool_name}: {error}"

    @property
    def stats(self) -> dict[str, int]:
        return {"allowed": self._allowed_count, "blocked": self._blocked_count}


def main() -> None:
    print(f"agent-gov version: {agent_gov.__version__}")

    if not _LANGCHAIN_AVAILABLE:
        print("langchain not installed — demonstrating governance wrapper only.")
        print("Install with: pip install langchain")

    # Step 1: Create governance engine
    engine = GovernanceEngine()

    # Step 2: Create governed tool wrappers
    search_tool = GovernedToolWrapper("search", engine)
    db_tool = GovernedToolWrapper("database_query", engine)
    delete_tool = GovernedToolWrapper("delete", engine)

    # Step 3: Execute tool calls through the governance gate
    print("\nExecuting governed tool calls:")
    calls: list[tuple[GovernedToolWrapper, dict[str, object]]] = [
        (search_tool, {"query": "quarterly revenue", "agent_role": "viewer", "estimated_cost": 0.01}),
        (db_tool, {"query": "drop table events", "agent_role": "operator", "estimated_cost": 0.01}),
        (search_tool, {"query": "user preferences", "agent_role": "operator", "estimated_cost": 0.02}),
        (delete_tool, {"target": "archived_logs", "agent_role": "viewer", "estimated_cost": 0.001}),
        (delete_tool, {"target": "temp_files", "agent_role": "admin", "estimated_cost": 0.001}),
    ]

    for tool, args in calls:
        result = tool.run(args)
        print(f"  {result}")

    # Step 4: Report governance summary
    print("\nGovernance stats:")
    for tool in [search_tool, db_tool, delete_tool]:
        print(f"  {tool._tool_name}: allowed={tool.stats['allowed']} blocked={tool.stats['blocked']}")


if __name__ == "__main__":
    main()

"""Audit subsystem — append-only event logging, querying, and search."""
from __future__ import annotations

from agent_gov.audit.entry import AuditEntry
from agent_gov.audit.logger import AuditLogger
from agent_gov.audit.reader import AuditReader
from agent_gov.audit.search import (
    FilterFn,
    aggregate_by_agent,
    aggregate_by_action_type,
    aggregate_by_policy,
    aggregate_verdicts,
    build_filter,
    search_entries,
)

__all__ = [
    "AuditEntry",
    "AuditLogger",
    "AuditReader",
    "FilterFn",
    "aggregate_by_action_type",
    "aggregate_by_agent",
    "aggregate_by_policy",
    "aggregate_verdicts",
    "build_filter",
    "search_entries",
]

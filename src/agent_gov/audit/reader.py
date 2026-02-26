"""AuditReader — read and filter audit log entries.

Provides a higher-level interface for querying the JSONL audit log with
support for date range, agent ID, action type, and verdict filtering.

Example
-------
::

    from datetime import datetime, timezone, timedelta
    from agent_gov.audit.reader import AuditReader

    reader = AuditReader("audit.jsonl")

    # Last 100 entries
    recent = reader.last(100)

    # Entries from a specific agent in the past day
    since = datetime.now(timezone.utc) - timedelta(days=1)
    entries = reader.query(agent_id="agent-1", since=since)

    # Statistics
    print(reader.stats())
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from agent_gov.audit.entry import AuditEntry
from agent_gov.audit.logger import AuditLogger, _apply_filters


class AuditReader:
    """Read-only interface for querying the audit log.

    Parameters
    ----------
    log_path:
        Path to the ``.jsonl`` audit log file.
    """

    def __init__(self, log_path: str | Path) -> None:
        self._logger = AuditLogger(log_path)

    @property
    def log_path(self) -> Path:
        """Return the path to the underlying audit log file."""
        return self._logger.log_path

    def all(self) -> list[AuditEntry]:
        """Return all audit entries in chronological order.

        Returns
        -------
        list[AuditEntry]
            All entries, oldest first.
        """
        return self._logger.read()

    def last(self, count: int) -> list[AuditEntry]:
        """Return the most recent ``count`` entries.

        Parameters
        ----------
        count:
            Maximum number of entries to return.

        Returns
        -------
        list[AuditEntry]
            Up to ``count`` entries, most recent last.
        """
        entries = self._logger.read()
        return entries[-count:] if count > 0 else []

    def query(
        self,
        *,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        verdict: Optional[str] = None,
        policy_name: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[AuditEntry]:
        """Return entries matching the supplied filter criteria.

        All provided filters are combined with AND logic.

        Parameters
        ----------
        agent_id:
            Filter by exact agent ID.
        action_type:
            Filter by exact action type string.
        verdict:
            Filter by verdict (``"pass"`` or ``"fail"``).
        policy_name:
            Filter by policy name.
        since:
            Return only entries at or after this UTC datetime.
        until:
            Return only entries at or before this UTC datetime.

        Returns
        -------
        list[AuditEntry]
            Matching entries in chronological order.
        """
        filters: dict[str, object] = {}
        if agent_id is not None:
            filters["agent_id"] = agent_id
        if action_type is not None:
            filters["action_type"] = action_type
        if verdict is not None:
            filters["verdict"] = verdict
        if policy_name is not None:
            filters["policy_name"] = policy_name
        if since is not None:
            filters["since"] = since
        if until is not None:
            filters["until"] = until

        entries = self._logger.read()
        return _apply_filters(entries, filters)

    def stats(self) -> dict[str, object]:
        """Return aggregate statistics about the audit log.

        Returns
        -------
        dict[str, object]
            Dictionary with keys:
            - ``total`` — total entry count
            - ``pass_count`` — entries with verdict ``"pass"``
            - ``fail_count`` — entries with verdict ``"fail"``
            - ``agents`` — sorted list of distinct agent IDs
            - ``action_types`` — sorted list of distinct action types
            - ``policies`` — sorted list of distinct policy names
            - ``earliest`` — ISO timestamp of earliest entry (or ``None``)
            - ``latest`` — ISO timestamp of latest entry (or ``None``)
        """
        entries = self._logger.read()
        if not entries:
            return {
                "total": 0,
                "pass_count": 0,
                "fail_count": 0,
                "agents": [],
                "action_types": [],
                "policies": [],
                "earliest": None,
                "latest": None,
            }

        pass_count = sum(1 for e in entries if e.verdict == "pass")
        fail_count = sum(1 for e in entries if e.verdict == "fail")
        agents = sorted({e.agent_id for e in entries})
        action_types = sorted({e.action_type for e in entries})
        policies = sorted({e.policy_name for e in entries})
        timestamps = [e.timestamp for e in entries]

        return {
            "total": len(entries),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "agents": agents,
            "action_types": action_types,
            "policies": policies,
            "earliest": min(timestamps).isoformat(),
            "latest": max(timestamps).isoformat(),
        }

"""AuditLogger — append-only JSONL audit log writer.

The logger appends one JSON line per audit entry to a file.  Append mode
ensures no existing entries are ever overwritten.  Thread-safety for same-
process concurrent writes is achieved via a threading lock; cross-process
safety depends on OS-level atomic appends (standard on POSIX, best-effort
on Windows).

Example
-------
::

    from agent_gov.audit.logger import AuditLogger
    from agent_gov.audit.entry import AuditEntry

    logger = AuditLogger("audit.jsonl")
    entry = AuditEntry(
        agent_id="agent-1",
        action_type="search",
        action_data={"query": "test"},
        verdict="pass",
        policy_name="standard",
    )
    logger.log(entry)
    print(f"Total entries: {logger.count()}")
"""
from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from agent_gov.audit.entry import AuditEntry


class AuditLogger:
    """Append-only JSONL audit event logger.

    Parameters
    ----------
    log_path:
        Path to the ``.jsonl`` audit log file.  The file is created on first
        write if it does not exist.
    """

    def __init__(self, log_path: str | Path) -> None:
        self._path = Path(log_path)
        self._lock = threading.Lock()

    @property
    def log_path(self) -> Path:
        """Return the resolved path to the log file."""
        return self._path

    def log(self, entry: AuditEntry) -> None:
        """Append a single audit entry to the log file.

        Parameters
        ----------
        entry:
            The entry to persist.
        """
        line = entry.to_json() + "\n"
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line)

    def log_from_report(
        self,
        report: object,
        agent_id: str,
        *,
        metadata: Optional[dict[str, str]] = None,
    ) -> AuditEntry:
        """Create and log an entry from an :class:`~agent_gov.policy.result.EvaluationReport`.

        Parameters
        ----------
        report:
            An :class:`~agent_gov.policy.result.EvaluationReport` instance.
        agent_id:
            The identifier of the agent that performed the action.
        metadata:
            Optional extra metadata to attach to the entry.

        Returns
        -------
        AuditEntry
            The entry that was logged.
        """
        # Import here to avoid circular imports at module level
        from agent_gov.policy.result import EvaluationReport

        if not isinstance(report, EvaluationReport):
            raise TypeError(
                f"Expected EvaluationReport, got {type(report).__name__}."
            )

        entry = AuditEntry(
            agent_id=agent_id,
            action_type=str(report.action.get("type", "unknown")),
            action_data=report.action,
            verdict="pass" if report.passed else "fail",
            policy_name=report.policy_name,
            timestamp=report.timestamp,
            metadata=metadata or {},
        )
        self.log(entry)
        return entry

    def read(self) -> list[AuditEntry]:
        """Read all audit entries from the log file.

        Returns
        -------
        list[AuditEntry]
            All entries in chronological order (oldest first).  Returns an
            empty list if the file does not exist.
        """
        if not self._path.exists():
            return []

        entries: list[AuditEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line_number, raw_line in enumerate(fh, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    entries.append(AuditEntry.from_json(stripped))
                except ValueError:
                    # Corrupted lines are skipped to keep the reader resilient
                    pass

        return entries

    def count(self) -> int:
        """Return the total number of valid entries in the log file.

        Returns
        -------
        int
            Entry count, or ``0`` if the file does not exist.
        """
        return len(self.read())

    def query(
        self,
        filters: dict[str, object],
    ) -> list[AuditEntry]:
        """Return entries matching all supplied filter criteria.

        Supported filter keys
        ----------------------
        agent_id : str
            Exact match on agent ID.
        action_type : str
            Exact match on action type.
        verdict : str
            Exact match on verdict (``"pass"`` or ``"fail"``).
        policy_name : str
            Exact match on policy name.
        since : datetime
            Only return entries at or after this datetime (UTC).
        until : datetime
            Only return entries at or before this datetime (UTC).

        Parameters
        ----------
        filters:
            Dict of filter criteria.  Unknown keys are ignored.

        Returns
        -------
        list[AuditEntry]
            Matching entries in chronological order.
        """
        entries = self.read()
        return _apply_filters(entries, filters)


def _apply_filters(
    entries: list[AuditEntry],
    filters: dict[str, object],
) -> list[AuditEntry]:
    """Apply filter criteria to a list of entries."""
    result = entries

    agent_id = filters.get("agent_id")
    if agent_id is not None:
        result = [e for e in result if e.agent_id == str(agent_id)]

    action_type = filters.get("action_type")
    if action_type is not None:
        result = [e for e in result if e.action_type == str(action_type)]

    verdict = filters.get("verdict")
    if verdict is not None:
        result = [e for e in result if e.verdict == str(verdict)]

    policy_name = filters.get("policy_name")
    if policy_name is not None:
        result = [e for e in result if e.policy_name == str(policy_name)]

    since = filters.get("since")
    if since is not None and isinstance(since, datetime):
        result = [e for e in result if e.timestamp >= since]

    until = filters.get("until")
    if until is not None and isinstance(until, datetime):
        result = [e for e in result if e.timestamp <= until]

    return result

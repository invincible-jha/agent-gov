"""Append-only evidence collector for compliance audits.

Records policy evaluation results as structured evidence entries and
provides query/export capabilities for downstream posture scoring and
report generation.

The collector is intentionally simple — it is an in-memory, append-only
log.  For persistence, call :meth:`EvidenceCollector.export_json`.

Usage
-----
::

    from datetime import datetime, timezone
    from agent_gov.dashboard.evidence_collector import EvidenceCollector, EvidenceEntry

    collector = EvidenceCollector()
    collector.record(EvidenceEntry(
        timestamp=datetime.now(timezone.utc),
        policy_id="eu-ai-act",
        rule_id="A13",
        result="pass",
        context={"agent": "my-agent", "action": "search"},
    ))
    entries = collector.query(policy_id="eu-ai-act")
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class EvidenceEntry:
    """An immutable record of a single policy evaluation result.

    Parameters
    ----------
    timestamp:
        UTC timestamp of the evaluation.
    policy_id:
        Identifier for the policy (e.g. ``"eu-ai-act"``, ``"gdpr"``).
    rule_id:
        Specific rule identifier within the policy (e.g. ``"A13"``).
    result:
        Evaluation outcome: ``"pass"``, ``"fail"``, or ``"skip"``.
    context:
        Arbitrary key/value context dict for this evaluation event.
    """

    timestamp: datetime
    policy_id: str
    rule_id: str
    result: str  # "pass", "fail", "skip"
    context: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Serialise the entry to a plain dictionary.

        Returns
        -------
        dict[str, object]
            JSON-serialisable representation.
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "policy_id": self.policy_id,
            "rule_id": self.rule_id,
            "result": self.result,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> EvidenceEntry:
        """Reconstruct an entry from a dictionary produced by :meth:`to_dict`.

        Parameters
        ----------
        data:
            Dictionary with at least ``timestamp``, ``policy_id``,
            ``rule_id``, ``result``, and ``context`` keys.

        Returns
        -------
        EvidenceEntry
        """
        raw_ts = data.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(str(raw_ts))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            ts = datetime.now(timezone.utc)

        return cls(
            timestamp=ts,
            policy_id=str(data.get("policy_id", "")),
            rule_id=str(data.get("rule_id", "")),
            result=str(data.get("result", "skip")),
            context=dict(data.get("context", {})),
        )


class EvidenceCollector:
    """Append-only in-memory evidence log for compliance audits.

    Thread safety
    -------------
    This implementation is not thread-safe.  In concurrent environments
    wrap calls in an external lock.

    Parameters
    ----------
    max_entries:
        Optional hard cap on stored entries.  When exceeded, the oldest
        entry is discarded (FIFO).  ``None`` means unbounded.
    """

    def __init__(self, max_entries: int | None = None) -> None:
        self._entries: list[EvidenceEntry] = []
        self._max_entries = max_entries

    # ------------------------------------------------------------------
    # Write interface
    # ------------------------------------------------------------------

    def record(self, entry: EvidenceEntry) -> None:
        """Append *entry* to the evidence log.

        Parameters
        ----------
        entry:
            The :class:`EvidenceEntry` to record.
        """
        self._entries.append(entry)
        if self._max_entries is not None and len(self._entries) > self._max_entries:
            self._entries.pop(0)

    def record_many(self, entries: list[EvidenceEntry]) -> None:
        """Append multiple entries in insertion order.

        Parameters
        ----------
        entries:
            Sequence of :class:`EvidenceEntry` objects to record.
        """
        for entry in entries:
            self.record(entry)

    # ------------------------------------------------------------------
    # Read interface
    # ------------------------------------------------------------------

    def query(
        self,
        policy_id: str | None = None,
        rule_id: str | None = None,
        result: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[EvidenceEntry]:
        """Return entries matching all supplied filter criteria.

        Parameters
        ----------
        policy_id:
            Filter to entries with this policy identifier.
        rule_id:
            Filter to entries with this rule identifier.
        result:
            Filter to entries with this result (``"pass"`` / ``"fail"`` / ``"skip"``).
        since:
            Include only entries at or after this UTC timestamp.
        until:
            Include only entries at or before this UTC timestamp.

        Returns
        -------
        list[EvidenceEntry]
            Matching entries in insertion order.
        """
        results: list[EvidenceEntry] = []
        for entry in self._entries:
            if policy_id is not None and entry.policy_id != policy_id:
                continue
            if rule_id is not None and entry.rule_id != rule_id:
                continue
            if result is not None and entry.result != result:
                continue
            if since is not None and entry.timestamp < since:
                continue
            if until is not None and entry.timestamp > until:
                continue
            results.append(entry)
        return results

    def all_entries(self) -> list[EvidenceEntry]:
        """Return all stored entries in insertion order.

        Returns
        -------
        list[EvidenceEntry]
        """
        return list(self._entries)

    @property
    def count(self) -> int:
        """Total number of entries currently stored."""
        return len(self._entries)

    def policy_ids(self) -> list[str]:
        """Return a sorted deduplicated list of all known policy IDs."""
        return sorted({e.policy_id for e in self._entries})

    def rule_ids(self, policy_id: str | None = None) -> list[str]:
        """Return a sorted deduplicated list of rule IDs.

        Parameters
        ----------
        policy_id:
            When provided, limit to rule IDs under this policy.
        """
        entries = self.query(policy_id=policy_id) if policy_id else self._entries
        return sorted({e.rule_id for e in entries})

    # ------------------------------------------------------------------
    # Export / import
    # ------------------------------------------------------------------

    def export_json(self, path: Path) -> None:
        """Write all entries to a JSONL file at *path*.

        Parameters
        ----------
        path:
            Destination file path.  Parent directories must exist.
        """
        with path.open("w", encoding="utf-8") as fh:
            for entry in self._entries:
                fh.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def export_dict(self) -> dict[str, object]:
        """Export all entries as a serialisable dictionary.

        Returns
        -------
        dict[str, object]
            Dictionary with ``entries`` list and ``count`` integer.
        """
        return {
            "count": self.count,
            "entries": [e.to_dict() for e in self._entries],
        }

    @classmethod
    def load_json(cls, path: Path) -> EvidenceCollector:
        """Load entries from a JSONL file produced by :meth:`export_json`.

        Parameters
        ----------
        path:
            Source file path.

        Returns
        -------
        EvidenceCollector
            New collector pre-populated with entries from the file.
        """
        collector = cls()
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    collector.record(EvidenceEntry.from_dict(data))
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue  # skip malformed lines
        return collector

    def clear(self) -> None:
        """Remove all stored entries from the collector."""
        self._entries.clear()


__all__ = [
    "EvidenceCollector",
    "EvidenceEntry",
]

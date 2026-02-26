"""Search and aggregation utilities for audit log entries.

Provides composable filter functions and aggregation helpers that work
over any list of :class:`~agent_gov.audit.entry.AuditEntry` objects,
independent of the underlying storage mechanism.

Example
-------
::

    from agent_gov.audit.search import build_filter, search_entries, aggregate_verdicts
    from agent_gov.audit.logger import AuditLogger

    logger = AuditLogger("audit.jsonl")
    entries = logger.read()

    # Build a reusable filter for a specific agent
    only_agent_1 = build_filter(agent_id="agent-1", verdict="fail")
    failures = search_entries(entries, only_agent_1, limit=50)

    # Count outcomes across all entries
    counts = aggregate_verdicts(entries)
    print(counts)  # {"pass": 42, "fail": 7}
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from agent_gov.audit.entry import AuditEntry

FilterFn = Callable[[AuditEntry], bool]


def build_filter(
    agent_id: Optional[str] = None,
    action_type: Optional[str] = None,
    verdict: Optional[str] = None,
    policy_name: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> FilterFn:
    """Build a composite filter function from optional criteria.

    All supplied criteria are combined with AND logic — an entry must
    satisfy every non-``None`` criterion to pass the filter.

    Parameters
    ----------
    agent_id:
        Exact match on :attr:`AuditEntry.agent_id`.
    action_type:
        Exact match on :attr:`AuditEntry.action_type`.
    verdict:
        Exact match on :attr:`AuditEntry.verdict` (``"pass"`` or ``"fail"``).
    policy_name:
        Exact match on :attr:`AuditEntry.policy_name`.
    since:
        Include only entries whose :attr:`AuditEntry.timestamp` is at or
        after this datetime.
    until:
        Include only entries whose :attr:`AuditEntry.timestamp` is at or
        before this datetime.

    Returns
    -------
    FilterFn
        A callable ``(AuditEntry) -> bool`` that returns ``True`` for
        entries matching all supplied criteria.
    """
    predicates: list[FilterFn] = []

    if agent_id is not None:
        predicates.append(lambda e, a=agent_id: e.agent_id == a)
    if action_type is not None:
        predicates.append(lambda e, at=action_type: e.action_type == at)
    if verdict is not None:
        predicates.append(lambda e, v=verdict: e.verdict == v)
    if policy_name is not None:
        predicates.append(lambda e, p=policy_name: e.policy_name == p)
    if since is not None:
        predicates.append(lambda e, s=since: e.timestamp >= s)
    if until is not None:
        predicates.append(lambda e, u=until: e.timestamp <= u)

    def combined(entry: AuditEntry) -> bool:
        return all(predicate(entry) for predicate in predicates)

    return combined


def search_entries(
    entries: list[AuditEntry],
    filter_fn: FilterFn,
    limit: int = 100,
) -> list[AuditEntry]:
    """Apply a filter function to a list of entries, returning up to ``limit`` matches.

    Entries are yielded in the same order they appear in ``entries``.

    Parameters
    ----------
    entries:
        Source list of audit entries to search.
    filter_fn:
        A callable produced by :func:`build_filter` or any function with
        the same signature ``(AuditEntry) -> bool``.
    limit:
        Maximum number of matching entries to return.  Use a large value
        (e.g. ``999_999``) to effectively return all matches.

    Returns
    -------
    list[AuditEntry]
        Matching entries in original order, capped at ``limit``.
    """
    results: list[AuditEntry] = []
    for entry in entries:
        if filter_fn(entry):
            results.append(entry)
            if len(results) >= limit:
                break
    return results


def aggregate_verdicts(entries: list[AuditEntry]) -> dict[str, int]:
    """Count entries grouped by verdict.

    Parameters
    ----------
    entries:
        Source list of audit entries.

    Returns
    -------
    dict[str, int]
        Mapping of verdict string to occurrence count, e.g.
        ``{"pass": 40, "fail": 10}``.  Only verdicts that actually
        appear in ``entries`` are included.
    """
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.verdict] = counts.get(entry.verdict, 0) + 1
    return counts


def aggregate_by_agent(entries: list[AuditEntry]) -> dict[str, list[AuditEntry]]:
    """Group entries by ``agent_id``.

    Parameters
    ----------
    entries:
        Source list of audit entries.

    Returns
    -------
    dict[str, list[AuditEntry]]
        Mapping of agent ID to the list of entries belonging to that
        agent, preserving original order within each group.
    """
    groups: dict[str, list[AuditEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.agent_id, []).append(entry)
    return groups


def aggregate_by_action_type(entries: list[AuditEntry]) -> dict[str, list[AuditEntry]]:
    """Group entries by ``action_type``.

    Parameters
    ----------
    entries:
        Source list of audit entries.

    Returns
    -------
    dict[str, list[AuditEntry]]
        Mapping of action type to the list of entries for that type.
    """
    groups: dict[str, list[AuditEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.action_type, []).append(entry)
    return groups


def aggregate_by_policy(entries: list[AuditEntry]) -> dict[str, list[AuditEntry]]:
    """Group entries by ``policy_name``.

    Parameters
    ----------
    entries:
        Source list of audit entries.

    Returns
    -------
    dict[str, list[AuditEntry]]
        Mapping of policy name to the list of entries evaluated under
        that policy.
    """
    groups: dict[str, list[AuditEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.policy_name, []).append(entry)
    return groups

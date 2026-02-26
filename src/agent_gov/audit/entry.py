"""AuditEntry — immutable record of a single governance evaluation event.

Each entry captures who (agent_id), what (action_type, action_data), when
(timestamp), and the resulting verdict from policy evaluation.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditEntry:
    """A single immutable audit log record.

    Attributes
    ----------
    agent_id:
        Unique identifier for the agent that performed the action.
    action_type:
        Short category/type string for the action (e.g. ``"search"``,
        ``"write"``, ``"delete"``).
    action_data:
        Full action payload as passed to the policy evaluator.
    verdict:
        Overall verdict: ``"pass"`` or ``"fail"``.
    policy_name:
        Name of the policy that produced the verdict.
    timestamp:
        UTC timestamp of the evaluation.  Auto-set to ``now()`` when not
        provided.
    metadata:
        Arbitrary additional context (run ID, environment, etc.).
    """

    agent_id: str
    action_type: str
    action_data: dict[str, object]
    verdict: str  # "pass" or "fail"
    policy_name: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialise the entry to a JSON string (single line, no newlines).

        The ``timestamp`` field is rendered as an ISO 8601 string.

        Returns
        -------
        str
            JSON representation suitable for JSONL storage.
        """
        data: dict[str, object] = {
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "verdict": self.verdict,
            "policy_name": self.policy_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_string: str) -> "AuditEntry":
        """Deserialise an entry from a JSON string.

        Parameters
        ----------
        json_string:
            A single JSONL line produced by :meth:`to_json`.

        Returns
        -------
        AuditEntry
            Reconstructed entry.

        Raises
        ------
        ValueError
            If the JSON is malformed or missing required fields.
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON audit entry: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("Audit entry JSON must be a JSON object (dict).")

        required_fields = {"agent_id", "action_type", "action_data", "verdict", "policy_name"}
        missing = required_fields - data.keys()
        if missing:
            raise ValueError(f"Audit entry missing required fields: {missing!r}")

        raw_ts = data.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(str(raw_ts))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)

        action_data = data.get("action_data", {})
        if not isinstance(action_data, dict):
            action_data = {}

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        return cls(
            agent_id=str(data["agent_id"]),
            action_type=str(data["action_type"]),
            action_data=action_data,
            verdict=str(data["verdict"]),
            policy_name=str(data["policy_name"]),
            timestamp=timestamp,
            metadata={str(k): str(v) for k, v in metadata.items()},
        )

    def __repr__(self) -> str:
        return (
            f"AuditEntry(agent_id={self.agent_id!r}, "
            f"action_type={self.action_type!r}, "
            f"verdict={self.verdict!r}, "
            f"timestamp={self.timestamp.isoformat()!r})"
        )

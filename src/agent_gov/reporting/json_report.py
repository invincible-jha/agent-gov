"""JsonReporter — render report payloads to JSON format.

Example
-------
::

    from agent_gov.reporting.json_report import JsonReporter
    from agent_gov.reporting.generator import ReportGenerator

    generator = ReportGenerator()
    payload = generator.governance_report(title="My Report")

    reporter = JsonReporter()
    json_string = reporter.render(payload)
    reporter.write(payload, "report.json")
"""
from __future__ import annotations

import json
from pathlib import Path


class JsonReporter:
    """Renders report payloads as formatted JSON strings.

    Parameters
    ----------
    indent:
        JSON indentation level.  Defaults to ``2``.
    ensure_ascii:
        When ``True`` non-ASCII characters are escaped.  Defaults to ``False``.
    """

    def __init__(self, indent: int = 2, ensure_ascii: bool = False) -> None:
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    def render(self, payload: dict[str, object]) -> str:
        """Render a report payload to a JSON string.

        Parameters
        ----------
        payload:
            Structured report data (produced by
            :class:`~agent_gov.reporting.generator.ReportGenerator`).

        Returns
        -------
        str
            Pretty-printed JSON string.
        """
        return json.dumps(
            payload,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
            default=str,  # Fallback for datetime and other non-JSON types
        )

    def write(self, payload: dict[str, object], output_path: str | Path) -> Path:
        """Render and write a report to a JSON file.

        Parameters
        ----------
        payload:
            Structured report data.
        output_path:
            Destination file path.  Parent directories are created if needed.

        Returns
        -------
        Path
            The resolved path of the written file.
        """
        resolved = Path(output_path).resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        json_content = self.render(payload)
        resolved.write_text(json_content, encoding="utf-8")
        return resolved

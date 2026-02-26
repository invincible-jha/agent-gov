"""MarkdownReporter — render report payloads to Markdown using Jinja2.

Jinja2 templates are loaded from the ``templates/`` directory adjacent to
this module.  Two templates are provided:

- ``governance_report.md.j2`` — governance/audit report
- ``compliance_report.md.j2`` — compliance framework report

Example
-------
::

    from agent_gov.reporting.markdown import MarkdownReporter
    from agent_gov.reporting.generator import ReportGenerator

    generator = ReportGenerator()
    payload = generator.governance_report(title="My Report")

    reporter = MarkdownReporter()
    markdown = reporter.render_governance(payload)
    reporter.write_governance(payload, "report.md")
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    _JINJA2_AVAILABLE = True
except ImportError:
    _JINJA2_AVAILABLE = False

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class MarkdownReporter:
    """Renders report payloads as Markdown using Jinja2 templates.

    Falls back to a built-in plain-text renderer when Jinja2 is not
    installed, so the class is always usable.
    """

    def __init__(self) -> None:
        self._env: Optional[object] = None
        if _JINJA2_AVAILABLE:
            self._env = Environment(  # type: ignore[assignment]
                loader=FileSystemLoader(str(_TEMPLATES_DIR)),
                autoescape=select_autoescape([]),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def render_governance(self, payload: dict[str, object]) -> str:
        """Render a governance report payload to Markdown.

        Parameters
        ----------
        payload:
            Structured governance report data produced by
            :class:`~agent_gov.reporting.generator.ReportGenerator`.

        Returns
        -------
        str
            Markdown-formatted report string.
        """
        if self._env is not None:
            from jinja2 import Environment

            env = self._env  # type: ignore[assignment]
            template = env.get_template("governance_report.md.j2")  # type: ignore[union-attr]
            return template.render(**payload)  # type: ignore[union-attr]
        return _fallback_governance(payload)

    def render_compliance(self, payload: dict[str, object]) -> str:
        """Render a compliance framework report payload to Markdown.

        Parameters
        ----------
        payload:
            Structured compliance report data.

        Returns
        -------
        str
            Markdown-formatted report string.
        """
        if self._env is not None:
            from jinja2 import Environment

            env = self._env  # type: ignore[assignment]
            template = env.get_template("compliance_report.md.j2")  # type: ignore[union-attr]
            return template.render(**payload)  # type: ignore[union-attr]
        return _fallback_compliance(payload)

    def write_governance(
        self,
        payload: dict[str, object],
        output_path: str | Path,
    ) -> Path:
        """Render and write a governance report to a Markdown file.

        Parameters
        ----------
        payload:
            Structured governance report data.
        output_path:
            Destination file path.

        Returns
        -------
        Path
            Resolved path of the written file.
        """
        resolved = Path(output_path).resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(self.render_governance(payload), encoding="utf-8")
        return resolved

    def write_compliance(
        self,
        payload: dict[str, object],
        output_path: str | Path,
    ) -> Path:
        """Render and write a compliance report to a Markdown file.

        Parameters
        ----------
        payload:
            Structured compliance report data.
        output_path:
            Destination file path.

        Returns
        -------
        Path
            Resolved path of the written file.
        """
        resolved = Path(output_path).resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(self.render_compliance(payload), encoding="utf-8")
        return resolved


def _fallback_governance(payload: dict[str, object]) -> str:
    """Plain-text Markdown fallback when Jinja2 is not installed."""
    lines: list[str] = [
        f"# {payload.get('title', 'Agent Governance Report')}",
        "",
        f"**Generated:** {payload.get('generated_at', 'N/A')}  ",
        f"**Policy:** {payload.get('policy_name', 'All')}  ",
        f"**Pass Rate:** {payload.get('pass_rate_percent', 'N/A')}%",
        "",
        "## Audit Summary",
        "",
    ]
    audit = payload.get("audit_summary", {})
    if isinstance(audit, dict):
        lines.append(f"- Total entries: {audit.get('total_entries', 0)}")
        lines.append(f"- Passed: {audit.get('pass_count', 0)}")
        lines.append(f"- Failed: {audit.get('fail_count', 0)}")
        agents = audit.get("agents", [])
        if isinstance(agents, list):
            lines.append(f"- Distinct agents: {len(agents)}")

    lines += ["", "## Evaluation Results", ""]
    evals = payload.get("evaluation_results", [])
    if isinstance(evals, list) and evals:
        for eval_result in evals:
            if not isinstance(eval_result, dict):
                continue
            status = "PASS" if eval_result.get("passed") else "FAIL"
            lines.append(
                f"- [{status}] `{eval_result.get('policy_name')}` "
                f"violations={eval_result.get('violation_count', 0)} "
                f"severity={eval_result.get('highest_severity', 'none')}"
            )
    else:
        lines.append("No evaluation results available.")

    return "\n".join(lines) + "\n"


def _fallback_compliance(payload: dict[str, object]) -> str:
    """Plain-text Markdown fallback when Jinja2 is not installed."""
    lines: list[str] = [
        f"# {payload.get('title', 'Compliance Report')}",
        "",
        f"**Generated:** {payload.get('generated_at', 'N/A')}  ",
        f"**Overall Score:** {payload.get('overall_score', 0.0):.1f}%",
        "",
    ]
    frameworks = payload.get("frameworks", [])
    if isinstance(frameworks, list):
        for framework_data in frameworks:
            if not isinstance(framework_data, dict):
                continue
            lines.append(f"## {framework_data.get('framework', 'Framework')}")
            lines.append("")
            lines.append(f"**Score:** {framework_data.get('score_percent', 0.0):.1f}%  ")
            lines.append(
                f"**Passed:** {framework_data.get('passed', 0)} / "
                f"{framework_data.get('total', 0)}"
            )
            lines.append("")
            results = framework_data.get("results", [])
            if isinstance(results, list):
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    status_icon = {"pass": "[x]", "fail": "[ ]", "unknown": "[?]"}.get(
                        result.get("status", "unknown"), "[?]"
                    )
                    lines.append(
                        f"- {status_icon} **{result.get('id')}** — "
                        f"{result.get('name')}"
                    )
            lines.append("")

    return "\n".join(lines)

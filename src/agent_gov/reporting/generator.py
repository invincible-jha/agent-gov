"""ReportGenerator — orchestrates governance and compliance report creation.

Combines evaluation results and audit data into structured report payloads
that can then be rendered by :class:`~agent_gov.reporting.markdown.MarkdownReporter`
or :class:`~agent_gov.reporting.json_report.JsonReporter`.

Example
-------
::

    from agent_gov.reporting.generator import ReportGenerator
    from agent_gov.audit.reader import AuditReader

    reader = AuditReader("audit.jsonl")
    generator = ReportGenerator(reader)

    payload = generator.governance_report(policy_name="standard")
    payload = generator.compliance_report(framework_reports=[eu_report, gdpr_report])
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agent_gov.audit.reader import AuditReader
from agent_gov.frameworks.base import FrameworkReport
from agent_gov.policy.result import EvaluationReport


class ReportGenerator:
    """Creates report payloads from evaluation results and audit data.

    Parameters
    ----------
    audit_reader:
        Optional :class:`~agent_gov.audit.reader.AuditReader` providing
        audit log data.  When ``None``, audit-related sections of reports
        are omitted.
    """

    def __init__(
        self,
        audit_reader: Optional[AuditReader] = None,
    ) -> None:
        self._reader = audit_reader

    def governance_report(
        self,
        *,
        policy_name: Optional[str] = None,
        evaluation_reports: Optional[list[EvaluationReport]] = None,
        title: str = "Agent Governance Report",
    ) -> dict[str, object]:
        """Build a governance report payload.

        Parameters
        ----------
        policy_name:
            Filter audit entries to a specific policy name.
        evaluation_reports:
            Recent :class:`~agent_gov.policy.result.EvaluationReport` objects
            to include in the report.
        title:
            Report title string.

        Returns
        -------
        dict[str, object]
            Structured report data suitable for rendering.
        """
        generated_at = datetime.now(timezone.utc).isoformat()

        # Build audit summary
        audit_summary: dict[str, object] = {}
        if self._reader is not None:
            all_stats = self._reader.stats()
            if policy_name:
                policy_entries = self._reader.query(policy_name=policy_name)
                policy_pass = sum(1 for e in policy_entries if e.verdict == "pass")
                policy_fail = sum(1 for e in policy_entries if e.verdict == "fail")
                audit_summary = {
                    "total_entries": len(policy_entries),
                    "pass_count": policy_pass,
                    "fail_count": policy_fail,
                    "agents": sorted({e.agent_id for e in policy_entries}),
                    "action_types": sorted({e.action_type for e in policy_entries}),
                }
            else:
                audit_summary = {
                    "total_entries": all_stats.get("total", 0),
                    "pass_count": all_stats.get("pass_count", 0),
                    "fail_count": all_stats.get("fail_count", 0),
                    "agents": all_stats.get("agents", []),
                    "action_types": all_stats.get("action_types", []),
                }

        # Build evaluation summary
        eval_summary: list[dict[str, object]] = []
        if evaluation_reports:
            for report in evaluation_reports:
                eval_summary.append({
                    "policy_name": report.policy_name,
                    "passed": report.passed,
                    "violation_count": report.violation_count,
                    "highest_severity": report.highest_severity,
                    "timestamp": report.timestamp.isoformat(),
                    "verdicts": [v.to_dict() for v in report.verdicts],
                })

        pass_rate: Optional[float] = None
        total = audit_summary.get("total_entries", 0)
        if isinstance(total, int) and total > 0:
            pass_count = audit_summary.get("pass_count", 0)
            if isinstance(pass_count, int):
                pass_rate = round(pass_count / total * 100, 2)

        return {
            "title": title,
            "generated_at": generated_at,
            "policy_name": policy_name,
            "audit_summary": audit_summary,
            "evaluation_results": eval_summary,
            "pass_rate_percent": pass_rate,
        }

    def compliance_report(
        self,
        *,
        framework_reports: list[FrameworkReport],
        title: str = "Compliance Framework Report",
    ) -> dict[str, object]:
        """Build a compliance framework report payload.

        Parameters
        ----------
        framework_reports:
            List of :class:`~agent_gov.frameworks.base.FrameworkReport` objects.
        title:
            Report title string.

        Returns
        -------
        dict[str, object]
            Structured report data suitable for rendering.
        """
        generated_at = datetime.now(timezone.utc).isoformat()

        frameworks_data: list[dict[str, object]] = [
            report.to_dict() for report in framework_reports
        ]

        overall_score: float = 0.0
        if framework_reports:
            overall_score = sum(r.score for r in framework_reports) / len(framework_reports)

        return {
            "title": title,
            "generated_at": generated_at,
            "overall_score": round(overall_score * 100, 2),
            "framework_count": len(framework_reports),
            "frameworks": frameworks_data,
        }

    def full_report(
        self,
        *,
        policy_name: Optional[str] = None,
        evaluation_reports: Optional[list[EvaluationReport]] = None,
        framework_reports: Optional[list[FrameworkReport]] = None,
        title: str = "Full Agent Governance and Compliance Report",
    ) -> dict[str, object]:
        """Build a combined governance and compliance report.

        Parameters
        ----------
        policy_name:
            Optional policy name filter for audit data.
        evaluation_reports:
            Optional list of evaluation reports.
        framework_reports:
            Optional list of framework check reports.
        title:
            Report title string.

        Returns
        -------
        dict[str, object]
            Combined report payload.
        """
        gov_report = self.governance_report(
            policy_name=policy_name,
            evaluation_reports=evaluation_reports,
            title=title,
        )
        compliance: dict[str, object] = {}
        if framework_reports:
            compliance = self.compliance_report(
                framework_reports=framework_reports,
                title=f"{title} — Compliance",
            )

        return {
            "title": title,
            "generated_at": gov_report["generated_at"],
            "governance": gov_report,
            "compliance": compliance,
        }

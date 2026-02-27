"""Cost reduction report generation for compliance cost analysis.

Renders :class:`~agent_gov.compliance_cost.calculator.CostReport` and
:class:`~agent_gov.compliance_cost.calculator.ComparisonReport` as
human-readable Markdown or plain-text summaries.

Usage
-----
::

    from agent_gov.compliance_cost.report import CostReportRenderer

    renderer = CostReportRenderer()
    print(renderer.to_markdown(report))
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_gov.compliance_cost.calculator import ComparisonReport, CostReport


class CostReportRenderer:
    """Renders cost-of-compliance reports as Markdown or plain text.

    Parameters
    ----------
    currency_symbol:
        Currency symbol prefix for monetary values (default ``"$"``).
    """

    def __init__(self, currency_symbol: str = "$") -> None:
        self._symbol = currency_symbol

    def to_markdown(self, report: CostReport) -> str:
        """Render a :class:`CostReport` as a Markdown document.

        Parameters
        ----------
        report:
            The cost report to render.

        Returns
        -------
        str
            Formatted Markdown string.
        """
        s = self._symbol
        lines: list[str] = [
            f"# Cost-of-Compliance Report — {report.framework.replace('_', ' ').title()}",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Requirements | {report.total_requirements} |",
            f"| Fully Automated | {report.automated_count} |",
            f"| Semi-Automated | {report.semi_automated_count} |",
            f"| Manual | {report.manual_count} |",
            f"| Hourly Rate | {s}{report.hourly_rate:,.2f} |",
            f"| Manual Total Hours | {report.total_hours_manual:,.1f} |",
            f"| Automated Total Hours | {report.total_hours_automated:,.1f} |",
            f"| **Manual Total Cost** | **{s}{report.total_cost_manual:,.0f}** |",
            f"| **Automated Total Cost** | **{s}{report.total_cost_with_automation:,.0f}** |",
            f"| **Savings** | **{report.savings_percentage:.1f}%** |",
            "",
            "## Requirement Detail",
            "",
            "| Requirement | Level | Manual Cost | Automated Cost | Savings |",
            "|-------------|-------|-------------|----------------|---------|",
        ]
        for detail in report.requirement_details:
            req_id = detail["requirement_id"]
            level = detail["automation_level"]
            c_m = detail["cost_manual"]
            c_a = detail["cost_automated"]
            savings = detail["savings"]
            lines.append(
                f"| {req_id} | {level} | {s}{c_m:,.0f} | {s}{c_a:,.0f} | {s}{savings:,.0f} |"
            )
        lines.append("")
        return "\n".join(lines)

    def to_text_summary(self, report: CostReport) -> str:
        """Render a compact single-paragraph text summary.

        Parameters
        ----------
        report:
            The cost report to summarise.

        Returns
        -------
        str
            Single-paragraph summary string.
        """
        return (
            f"{report.framework.replace('_', ' ').upper()}: "
            f"{report.total_requirements} requirements, "
            f"{report.automated_count} fully automated, "
            f"{report.semi_automated_count} semi-automated, "
            f"{report.manual_count} manual. "
            f"Manual cost: {self._symbol}{report.total_cost_manual:,.0f} "
            f"| Automated cost: {self._symbol}{report.total_cost_with_automation:,.0f} "
            f"| Savings: {report.savings_percentage:.1f}%."
        )

    def comparison_to_markdown(self, comparison: ComparisonReport) -> str:
        """Render a :class:`ComparisonReport` as a Markdown comparison table.

        Parameters
        ----------
        comparison:
            The comparison report to render.

        Returns
        -------
        str
            Formatted Markdown comparison document.
        """
        s = self._symbol
        lines: list[str] = [
            f"# Compliance Cost Comparison — {comparison.framework.replace('_', ' ').title()}",
            "",
            "## Scenario Comparison",
            "",
            "| Scenario | Automated | Manual | Total Cost | Savings |",
            "|----------|-----------|--------|------------|---------|",
        ]
        for label, report in comparison.scenarios:
            lines.append(
                f"| {label} | {report.automated_count} | {report.manual_count} "
                f"| {s}{report.total_cost_with_automation:,.0f} "
                f"| {report.savings_percentage:.1f}% |"
            )
        lines.append("")

        best = comparison.best_scenario()
        if best:
            lines.append(f"**Best scenario:** {best[0]} (lowest total cost)")
            lines.append("")

        return "\n".join(lines)


__all__ = [
    "CostReportRenderer",
]

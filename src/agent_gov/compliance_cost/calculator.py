"""Cost-of-compliance calculator.

Maps compliance requirements to automated vs manual labour categories
and computes cost estimates for each.  Produces a structured
:class:`CostReport` and supports scenario comparison via
:meth:`ComplianceCostCalculator.compare_scenarios`.

Algorithms used
---------------
All cost calculations are basic multiplication (hours × rate).  No
proprietary scoring, ML weights, or trade-secret logic is included.

Usage
-----
::

    from agent_gov.compliance_cost.calculator import ComplianceCostCalculator

    calc = ComplianceCostCalculator(hourly_rate=150.0)
    report = calc.calculate("eu_ai_act", automation_coverage={})
    print(f"Savings: {report.savings_percentage:.1f}%")
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComplianceRequirement:
    """A single compliance requirement with cost metadata.

    Parameters
    ----------
    framework:
        Regulatory framework (``"eu_ai_act"``, ``"gdpr"``, ``"hipaa"``).
    requirement_id:
        Short unique identifier within the framework.
    description:
        Plain-language description of the requirement.
    automation_level:
        Current automation status.  One of:
        - ``"fully_automated"`` — tooling handles end-to-end.
        - ``"semi_automated"`` — tooling assists but human review needed.
        - ``"manual"`` — entirely manual process.
    estimated_hours_manual:
        Analyst-hours when the requirement is handled entirely manually.
    estimated_hours_automated:
        Analyst-hours when automated tooling is in use.
    """

    framework: str
    requirement_id: str
    description: str
    automation_level: str
    estimated_hours_manual: float
    estimated_hours_automated: float

    def cost_manual(self, hourly_rate: float) -> float:
        """Return the cost in currency units when handled manually."""
        return self.estimated_hours_manual * hourly_rate

    def cost_automated(self, hourly_rate: float) -> float:
        """Return the cost in currency units when automated."""
        return self.estimated_hours_automated * hourly_rate

    def savings(self, hourly_rate: float) -> float:
        """Return the cost saving from automation."""
        return self.cost_manual(hourly_rate) - self.cost_automated(hourly_rate)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "framework": self.framework,
            "requirement_id": self.requirement_id,
            "description": self.description,
            "automation_level": self.automation_level,
            "estimated_hours_manual": self.estimated_hours_manual,
            "estimated_hours_automated": self.estimated_hours_automated,
        }


@dataclass(frozen=True)
class CostReport:
    """Cost-of-compliance report for a single framework and automation scenario.

    Parameters
    ----------
    framework:
        The regulatory framework being reported on.
    total_requirements:
        Total number of requirements in the framework.
    automated_count:
        Count of requirements classified as ``"fully_automated"`` in this scenario.
    semi_automated_count:
        Count of ``"semi_automated"`` requirements.
    manual_count:
        Count of ``"manual"`` requirements.
    total_hours_manual:
        Sum of manual-mode hours across all requirements.
    total_hours_automated:
        Sum of automated-mode hours across all requirements.
    total_cost_manual:
        Total cost (currency units) under fully manual mode.
    total_cost_with_automation:
        Total cost (currency units) under the current automation scenario.
    savings_percentage:
        Percentage cost reduction: ``(1 - automated_cost / manual_cost) * 100``.
    hourly_rate:
        Hourly rate used in the calculation.
    requirement_details:
        Tuple of per-requirement cost lines.
    """

    framework: str
    total_requirements: int
    automated_count: int
    semi_automated_count: int
    manual_count: int
    total_hours_manual: float
    total_hours_automated: float
    total_cost_manual: float
    total_cost_with_automation: float
    savings_percentage: float
    hourly_rate: float
    requirement_details: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "framework": self.framework,
            "total_requirements": self.total_requirements,
            "automated_count": self.automated_count,
            "semi_automated_count": self.semi_automated_count,
            "manual_count": self.manual_count,
            "total_hours_manual": round(self.total_hours_manual, 2),
            "total_hours_automated": round(self.total_hours_automated, 2),
            "total_cost_manual": round(self.total_cost_manual, 2),
            "total_cost_with_automation": round(self.total_cost_with_automation, 2),
            "savings_percentage": round(self.savings_percentage, 2),
            "hourly_rate": self.hourly_rate,
            "requirement_details": list(self.requirement_details),
        }

    def summary(self) -> str:
        """Return a one-line human-readable summary."""
        return (
            f"Framework: {self.framework} | "
            f"Requirements: {self.total_requirements} | "
            f"Manual cost: ${self.total_cost_manual:,.0f} | "
            f"Automated cost: ${self.total_cost_with_automation:,.0f} | "
            f"Savings: {self.savings_percentage:.1f}%"
        )


@dataclass(frozen=True)
class ComparisonReport:
    """Comparison of multiple automation scenarios for a single framework.

    Parameters
    ----------
    framework:
        The regulatory framework being compared.
    scenarios:
        Ordered tuple of (label, CostReport) pairs.
    """

    framework: str
    scenarios: tuple[tuple[str, CostReport], ...]

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "framework": self.framework,
            "scenarios": [
                {"label": label, "report": report.to_dict()}
                for label, report in self.scenarios
            ],
        }

    def best_scenario(self) -> tuple[str, CostReport] | None:
        """Return the scenario with the lowest total automated cost."""
        if not self.scenarios:
            return None
        return min(self.scenarios, key=lambda pair: pair[1].total_cost_with_automation)


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


class ComplianceCostCalculator:
    """Maps compliance requirements to cost estimates.

    Parameters
    ----------
    hourly_rate:
        Default labour rate in currency units per hour (default 150.0 USD/hr).
    """

    def __init__(self, hourly_rate: float = 150.0) -> None:
        if hourly_rate <= 0:
            raise ValueError(f"hourly_rate must be positive, got {hourly_rate}")
        self._hourly_rate = hourly_rate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        framework: str,
        automation_coverage: dict[str, str],
    ) -> CostReport:
        """Calculate compliance costs for *framework* under the given scenario.

        Parameters
        ----------
        framework:
            Framework name: ``"eu_ai_act"``, ``"gdpr"``, or ``"hipaa"``.
        automation_coverage:
            Mapping of requirement_id to overridden automation_level string.
            Requirements not in this dict use their default level from the
            framework catalogue.

        Returns
        -------
        CostReport
            Detailed cost breakdown.
        """
        from agent_gov.compliance_cost.framework_maps import get_requirements

        requirements = get_requirements(framework)
        return self._compute_report(framework, requirements, automation_coverage)

    def compare_scenarios(
        self,
        framework: str,
        scenarios: list[dict[str, object]],  # each: {"label": str, "automation_coverage": dict[str, str]}
    ) -> ComparisonReport:
        """Compare multiple automation scenarios for the same framework.

        Parameters
        ----------
        framework:
            Framework name.
        scenarios:
            List of scenario dicts, each with:
            - ``"label"`` (str): human-readable scenario name.
            - ``"automation_coverage"`` (dict[str, str]): per-requirement
              automation level overrides (same format as :meth:`calculate`).

        Returns
        -------
        ComparisonReport
            Structured comparison of all scenarios.
        """
        pairs: list[tuple[str, CostReport]] = []
        for scenario in scenarios:
            label = str(scenario.get("label", "unnamed"))
            coverage = dict(scenario.get("automation_coverage", {}))
            report = self.calculate(framework, coverage)
            pairs.append((label, report))

        return ComparisonReport(
            framework=framework,
            scenarios=tuple(pairs),
        )

    def calculate_with_custom_requirements(
        self,
        requirements: list[ComplianceRequirement],
        automation_coverage: dict[str, str],
    ) -> CostReport:
        """Calculate costs from a custom list of requirements.

        Parameters
        ----------
        requirements:
            List of :class:`ComplianceRequirement` objects.
        automation_coverage:
            Per-requirement automation level overrides.

        Returns
        -------
        CostReport
        """
        framework = requirements[0].framework if requirements else "custom"
        return self._compute_report(framework, requirements, automation_coverage)

    @property
    def hourly_rate(self) -> float:
        """Return the configured hourly rate."""
        return self._hourly_rate

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_report(
        self,
        framework: str,
        requirements: list[ComplianceRequirement],
        automation_coverage: dict[str, str],
    ) -> CostReport:
        """Compute cost report from requirements and automation coverage."""
        automated_count = 0
        semi_automated_count = 0
        manual_count = 0
        total_hours_manual = 0.0
        total_hours_automated = 0.0
        details: list[dict[str, object]] = []

        for req in requirements:
            # Apply coverage override or use default
            effective_level = automation_coverage.get(req.requirement_id, req.automation_level)

            # Determine effective hours based on level
            hours_used = self._hours_for_level(
                req,
                effective_level,
            )

            cost_manual = req.cost_manual(self._hourly_rate)
            cost_with_automation = hours_used * self._hourly_rate

            if effective_level == "fully_automated":
                automated_count += 1
            elif effective_level == "semi_automated":
                semi_automated_count += 1
            else:
                manual_count += 1

            total_hours_manual += req.estimated_hours_manual
            total_hours_automated += hours_used

            details.append({
                "requirement_id": req.requirement_id,
                "description": req.description,
                "automation_level": effective_level,
                "hours_manual": req.estimated_hours_manual,
                "hours_automated": hours_used,
                "cost_manual": round(cost_manual, 2),
                "cost_automated": round(cost_with_automation, 2),
                "savings": round(cost_manual - cost_with_automation, 2),
            })

        total_cost_manual = total_hours_manual * self._hourly_rate
        total_cost_automated = total_hours_automated * self._hourly_rate
        savings_pct = (
            (1.0 - total_cost_automated / total_cost_manual) * 100.0
            if total_cost_manual > 0
            else 0.0
        )

        return CostReport(
            framework=framework,
            total_requirements=len(requirements),
            automated_count=automated_count,
            semi_automated_count=semi_automated_count,
            manual_count=manual_count,
            total_hours_manual=total_hours_manual,
            total_hours_automated=total_hours_automated,
            total_cost_manual=total_cost_manual,
            total_cost_with_automation=total_cost_automated,
            savings_percentage=savings_pct,
            hourly_rate=self._hourly_rate,
            requirement_details=tuple(details),
        )

    def _hours_for_level(
        self,
        req: ComplianceRequirement,
        effective_level: str,
    ) -> float:
        """Return the applicable hours estimate given the effective automation level."""
        if effective_level == "fully_automated":
            return req.estimated_hours_automated
        if effective_level == "semi_automated":
            # Blend: midpoint of manual and automated hours
            return (req.estimated_hours_manual + req.estimated_hours_automated) / 2.0
        # manual
        return req.estimated_hours_manual


__all__ = [
    "ComparisonReport",
    "ComplianceCostCalculator",
    "ComplianceRequirement",
    "CostReport",
]

"""Abstract base class for compliance frameworks.

A compliance framework is a structured checklist of requirements.  Each
requirement maps to a :class:`ChecklistItem`.  After running a compliance
check the results are collected into a :class:`FrameworkReport`.

Example
-------
::

    from agent_gov.frameworks.base import ComplianceFramework, FrameworkReport

    class MyFramework(ComplianceFramework):
        name = "my-framework"
        version = "1.0"

        def checklist(self) -> list[ChecklistItem]:
            return [
                ChecklistItem(id="C1", name="Logging enabled", description="..."),
            ]

        def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
            items = self.checklist()
            results = []
            for item in items:
                status = "pass" if evidence.get(item.id) else "fail"
                results.append(CheckResult(item=item, status=status))
            return FrameworkReport(framework=self.name, results=results)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChecklistItem:
    """A single requirement in a compliance checklist.

    Attributes
    ----------
    id:
        Short, unique identifier (e.g. ``"A6"`` for EU AI Act Article 6).
    name:
        Concise human-readable requirement name.
    description:
        Full description of what the requirement entails.
    category:
        Optional grouping category (e.g. ``"transparency"``, ``"risk"``).
    """

    id: str
    name: str
    description: str
    category: str = ""


@dataclass
class CheckResult:
    """Result of evaluating a single :class:`ChecklistItem`.

    Attributes
    ----------
    item:
        The checklist item that was evaluated.
    status:
        One of ``"pass"``, ``"fail"``, or ``"unknown"``.
    evidence:
        Human-readable evidence string explaining how the status was determined.
    """

    item: ChecklistItem
    status: str  # "pass", "fail", "unknown"
    evidence: str = ""


@dataclass
class FrameworkReport:
    """Aggregated results of a full compliance framework check.

    Attributes
    ----------
    framework:
        Name of the framework that produced this report.
    results:
        One :class:`CheckResult` per :class:`ChecklistItem` in the checklist.
    """

    framework: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def score(self) -> float:
        """Compliance score as a fraction of items that passed (0.0–1.0).

        Returns ``0.0`` when there are no results.
        """
        if not self.results:
            return 0.0
        passed = sum(1 for result in self.results if result.status == "pass")
        return passed / len(self.results)

    @property
    def score_percent(self) -> float:
        """Compliance score as a percentage (0.0–100.0)."""
        return self.score * 100.0

    @property
    def passed_count(self) -> int:
        """Number of items with status ``"pass"``."""
        return sum(1 for r in self.results if r.status == "pass")

    @property
    def failed_count(self) -> int:
        """Number of items with status ``"fail"``."""
        return sum(1 for r in self.results if r.status == "fail")

    @property
    def unknown_count(self) -> int:
        """Number of items with status ``"unknown"``."""
        return sum(1 for r in self.results if r.status == "unknown")

    def to_dict(self) -> dict[str, object]:
        """Serialise the report to a plain dictionary."""
        return {
            "framework": self.framework,
            "score": self.score,
            "score_percent": self.score_percent,
            "total": len(self.results),
            "passed": self.passed_count,
            "failed": self.failed_count,
            "unknown": self.unknown_count,
            "results": [
                {
                    "id": r.item.id,
                    "name": r.item.name,
                    "category": r.item.category,
                    "status": r.status,
                    "evidence": r.evidence,
                }
                for r in self.results
            ],
        }


class ComplianceFramework(ABC):
    """Abstract base class for all compliance framework implementations.

    Class Attributes
    ----------------
    name:
        Unique identifier for this framework (e.g. ``"eu-ai-act"``).
    version:
        Version string of the framework specification.
    description:
        Human-readable description of what this framework covers.
    """

    name: str = ""
    version: str = "1.0"
    description: str = ""

    @abstractmethod
    def checklist(self) -> list[ChecklistItem]:
        """Return the full ordered list of compliance checklist items."""

    @abstractmethod
    def run_check(self, evidence: dict[str, object]) -> FrameworkReport:
        """Evaluate evidence against every item in the checklist.

        Parameters
        ----------
        evidence:
            Key/value mapping where keys correspond to checklist item IDs
            or other evidence fields recognised by this framework.

        Returns
        -------
        FrameworkReport
            Report containing one :class:`CheckResult` per checklist item.
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, version={self.version!r})"

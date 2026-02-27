"""Multi-framework compliance mapping — cross-framework requirement overlap analysis."""
from __future__ import annotations

from agent_gov.multi_framework.mapper import (
    CrossFrameworkMapper,
    FrameworkRequirement,
    MappingResult,
    RequirementMatch,
)
from agent_gov.multi_framework.overlap_analyzer import (
    ControlGroup,
    OverlapAnalyzer,
    OverlapReport,
    SharedControl,
)

__all__ = [
    "CrossFrameworkMapper",
    "FrameworkRequirement",
    "MappingResult",
    "RequirementMatch",
    "ControlGroup",
    "OverlapAnalyzer",
    "OverlapReport",
    "SharedControl",
]

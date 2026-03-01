"""agent-gov live compliance dashboard subpackage.

Provides evidence collection, posture scoring, report generation, and a
full single-page web dashboard for AI governance compliance monitoring.
"""
from __future__ import annotations

from agent_gov.dashboard.evidence_collector import EvidenceCollector, EvidenceEntry
from agent_gov.dashboard.posture_scorer import PostureScore, PostureScorer
from agent_gov.dashboard.report_generator import ReportGenerator
from agent_gov.dashboard.server import WebDashboardServer

__all__ = [
    "EvidenceCollector",
    "EvidenceEntry",
    "PostureScore",
    "PostureScorer",
    "ReportGenerator",
    "WebDashboardServer",
]

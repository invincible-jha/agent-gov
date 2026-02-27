"""agent-gov — AI agent governance and compliance engine with policy enforcement.

Public API
----------
The stable public surface is everything exported from this module.
Anything inside submodules not re-exported here is considered private
and may change without notice.

Example
-------
>>> import agent_gov
>>> agent_gov.__version__
'0.1.0'
>>> from agent_gov import PolicyEvaluator, AuditLogger, AuditEntry
"""
from __future__ import annotations

# Audit subsystem
from agent_gov.audit.entry import AuditEntry
from agent_gov.audit.logger import AuditLogger
from agent_gov.audit.reader import AuditReader
from agent_gov.audit.search import (
    FilterFn,
    aggregate_by_action_type,
    aggregate_by_agent,
    aggregate_by_policy,
    aggregate_verdicts,
    build_filter,
    search_entries,
)

# Compliance frameworks
from agent_gov.frameworks.base import (
    ChecklistItem,
    CheckResult,
    ComplianceFramework,
    FrameworkReport,
)
from agent_gov.frameworks.eu_ai_act import EuAiActFramework
from agent_gov.frameworks.gdpr import GdprFramework
from agent_gov.frameworks.hipaa import HipaaFramework
from agent_gov.frameworks.soc2 import Soc2Framework

# Plugin system
from agent_gov.plugins.registry import PluginRegistry

# Policy engine
from agent_gov.policy.evaluator import PolicyEvaluator
from agent_gov.policy.loader import PolicyLoader
from agent_gov.policy.result import EvaluationReport
from agent_gov.policy.rule import PolicyRule, RuleVerdict
from agent_gov.policy.schema import PolicyConfig, RuleConfig, Severity

# Reporting
from agent_gov.reporting.generator import ReportGenerator
from agent_gov.reporting.json_report import JsonReporter
from agent_gov.reporting.markdown import MarkdownReporter
from agent_gov.reporting.templates import get_template, list_templates, write_template

# Built-in rules
from agent_gov.rules.cost_limit import CostLimitRule
from agent_gov.rules.keyword_block import KeywordBlockRule
from agent_gov.rules.pii_check import PiiCheckRule
from agent_gov.rules.role_check import RoleCheckRule

__version__: str = "0.1.0"

from agent_gov.convenience import GovernanceEngine

__all__ = [
    "GovernanceEngine",
    # Version
    "__version__",
    # Audit
    "AuditEntry",
    "AuditLogger",
    "AuditReader",
    "FilterFn",
    "aggregate_by_action_type",
    "aggregate_by_agent",
    "aggregate_by_policy",
    "aggregate_verdicts",
    "build_filter",
    "search_entries",
    # Frameworks
    "ChecklistItem",
    "CheckResult",
    "ComplianceFramework",
    "EuAiActFramework",
    "FrameworkReport",
    "GdprFramework",
    "HipaaFramework",
    "Soc2Framework",
    # Plugins
    "PluginRegistry",
    # Policy
    "EvaluationReport",
    "PolicyConfig",
    "PolicyEvaluator",
    "PolicyLoader",
    "PolicyRule",
    "RuleConfig",
    "RuleVerdict",
    "Severity",
    # Reporting
    "JsonReporter",
    "MarkdownReporter",
    "ReportGenerator",
    "get_template",
    "list_templates",
    "write_template",
    # Rules
    "CostLimitRule",
    "KeywordBlockRule",
    "PiiCheckRule",
    "RoleCheckRule",
]

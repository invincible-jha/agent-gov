# agent-gov

AI Agent Governance & Compliance Engine — policy enforcement, audit logging, EU AI Act compliance.

[![CI](https://github.com/invincible-jha/agent-gov/actions/workflows/ci.yaml/badge.svg)](https://github.com/invincible-jha/agent-gov/actions/workflows/ci.yaml)
[![PyPI version](https://img.shields.io/pypi/v/agent-gov.svg)](https://pypi.org/project/agent-gov/)
[![Python versions](https://img.shields.io/pypi/pyversions/agent-gov.svg)](https://pypi.org/project/agent-gov/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

---

## Installation

```bash
pip install agent-gov
```

Verify the installation:

```bash
agent-gov version
```

---

## Quick Start

```python
from pathlib import Path
import agent_gov
from agent_gov import (
    AuditLogger,
    AuditReader,
    EuAiActFramework,
    GdprFramework,
    PolicyEvaluator,
    PolicyLoader,
    ReportGenerator,
)

# Load the standard policy pack bundled with agent-gov
packs_dir = Path(agent_gov.__file__).parent / "packs"
loader = PolicyLoader()
policy = loader.load_file(packs_dir / "standard.yaml")
print(f"Loaded policy: {policy.name!r} (v{policy.version})")

evaluator = PolicyEvaluator()

# Evaluate a safe action — should pass
safe_action: dict[str, object] = {
    "type": "search",
    "query": "quarterly revenue trends",
    "agent_role": "operator",
    "cost": 0.02,
}
report = evaluator.evaluate(policy, safe_action)
print(f"Safe action: {report.summary()}")

# Evaluate a risky action — blocked keyword detected
risky_action: dict[str, object] = {
    "type": "database_query",
    "query": "drop table users",
    "agent_role": "operator",
    "cost": 0.01,
}
report = evaluator.evaluate(policy, risky_action)
print(f"Risky action: {report.summary()}")
for verdict in report.failed_verdicts:
    print(f"  FAIL [{verdict.severity}] {verdict.rule_name}: {verdict.message}")

# Check EU AI Act compliance
eu_framework = EuAiActFramework()
eu_evidence: dict[str, object] = {
    "A6": {"status": "pass", "evidence": "System classified as limited risk."},
    "A13": {"status": "pass", "evidence": "Model card published."},
    "A14": {"status": "pass", "evidence": "Human review required for critical decisions."},
}
eu_report = eu_framework.run_check(eu_evidence)
print(f"EU AI Act score: {eu_report.score_percent:.1f}%")
```

---

## Key Features

- **Declarative YAML policies** — `PolicyConfig` with versioned rules, per-rule severity, enable/disable flags, and audit metadata
- **Policy evaluation engine** — evaluates action contexts using AND/OR condition logic with operators including `contains_pii`, `matches`, `greater_than`, and `in_list`
- **Four built-in rule types** — PII check, role check, cost limit, and keyword block, each implementing the `PolicyRule` ABC and registered via the plugin system
- **Compliance framework stubs** — EU AI Act, GDPR, HIPAA, and SOC 2 that map rule violations to specific regulatory articles and controls
- **Append-only audit logger** — structured JSON entries with a search API for querying the audit trail by agent ID, policy name, and time range
- **Compliance report generator** — produces JSON and Markdown summaries grouped by framework and severity
- **agentcore bridge** — hooks `PolicyEngine` evaluation into the `EventBus` lifecycle so governance runs transparently alongside agent execution

---

## Links

- [GitHub Repository](https://github.com/invincible-jha/agent-gov)
- [PyPI Package](https://pypi.org/project/agent-gov/)
- [Architecture](architecture.md)
- [Changelog](https://github.com/invincible-jha/agent-gov/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/invincible-jha/agent-gov/blob/main/CONTRIBUTING.md)

---

> Part of the [AumOS](https://github.com/aumos-ai) open-source agent infrastructure portfolio.

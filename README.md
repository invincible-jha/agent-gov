# agent-gov

AI agent governance and compliance engine with policy enforcement

[![CI](https://github.com/aumos-ai/agent-gov/actions/workflows/ci.yaml/badge.svg)](https://github.com/aumos-ai/agent-gov/actions/workflows/ci.yaml)
[![PyPI version](https://img.shields.io/pypi/v/agent-gov.svg)](https://pypi.org/project/agent-gov/)
[![Python versions](https://img.shields.io/pypi/pyversions/agent-gov.svg)](https://pypi.org/project/agent-gov/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Part of the [AumOS](https://github.com/aumos-ai) open-source agent infrastructure portfolio.

---

## Features

- Declarative YAML policy schema (`PolicyConfig`) with versioned rules, per-rule severity, enable/disable flags, and arbitrary metadata for audit trails
- `PolicyEngine` evaluates action contexts against ordered rule lists using AND/OR condition logic with operators including `contains_pii`, `matches`, `greater_than`, and `in_list`
- Four built-in rule types — PII check, role check, cost limit, and keyword block — each implementing the `PolicyRule` ABC and registered via the plugin system
- Compliance framework stubs for EU AI Act, GDPR, HIPAA, and SOC 2 that map rule violations to specific regulatory articles and controls
- Append-only audit logger with structured JSON entries and a search API for querying the audit trail by agent ID, policy name, and time range
- Compliance report generator producing JSON and Markdown summaries grouped by framework and severity
- `agentcore` bridge that hooks `PolicyEngine` evaluation into the `EventBus` lifecycle so governance runs transparently alongside agent execution

## Current Limitations

> **Transparency note**: We list known limitations to help you evaluate fit.

- **Evaluation**: Rule-based policy evaluation only. No ML-powered policy learning.
- **Adapters**: Governance overlays (observability/compliance on top of frameworks), not provider integrations.
- **Frameworks**: EU AI Act, GDPR, HIPAA, SOC2, ISO 42001, NIST AI RMF — no sector-specific frameworks yet.

## Quick Start

Install from PyPI:

```bash
pip install agent-gov
```

Verify the installation:

```bash
agent-gov version
```

Basic usage:

```python
import agent_gov

# See examples/01_quickstart.py for a working example
```

## Documentation

- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Examples](examples/README.md)

## Enterprise Upgrade

For production deployments requiring SLA-backed support and advanced
integrations, contact the maintainers or see the commercial extensions documentation.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
before opening a pull request.

## License

Apache 2.0 — see [LICENSE](LICENSE) for full terms.

---

Part of [AumOS](https://github.com/aumos-ai) — open-source agent infrastructure.

# Examples

| # | Example | Description |
|---|---------|-------------|
| 01 | [Quickstart](01_quickstart.py) | Policy evaluation, compliance checks, and audit logging |
| 02 | [Policy Rules](02_policy_rules.py) | Custom policies with keyword block, PII, cost, and role rules |
| 03 | [Compliance Frameworks](03_compliance_frameworks.py) | EU AI Act, GDPR, HIPAA, and SOC 2 checks |
| 04 | [Audit Search](04_audit_search.py) | Search, filter, and aggregate audit log entries |
| 05 | [Reporting](05_reporting.py) | Generate JSON and Markdown governance reports |
| 06 | [LangChain Gov](06_langchain_gov.py) | Governance gate for LangChain tool calls |
| 07 | [CrewAI Gov](07_crewai_gov.py) | Governance-enforced CrewAI task execution |

## Running the examples

```bash
pip install agent-gov
python examples/01_quickstart.py
```

For framework integrations:

```bash
pip install langchain   # for example 06
pip install crewai      # for example 07
```

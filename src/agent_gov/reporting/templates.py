"""Built-in YAML policy templates for agent-gov.

Provides ready-to-use governance policy templates at three maturity levels:

- ``minimal`` — logging-only baseline with a single keyword-block rule.
- ``basic`` — standard PII and keyword protection suitable for most agents.
- ``full`` — full-featured policy with role gating, cost controls,
  PII protection, and an expanded keyword blocklist.

Example
-------
::

    from pathlib import Path
    from agent_gov.reporting.templates import write_template, list_templates

    # List available templates
    print(list_templates())  # ['basic', 'full', 'minimal']

    # Write the full template to disk for customisation
    write_template("full", Path("policies/full-policy.yaml"))
"""
from __future__ import annotations

from pathlib import Path

TEMPLATES: dict[str, str] = {
    "minimal": """\
# Minimal governance policy (logging only)
name: minimal-policy
version: "1.0"
rules:
  - type: keyword_block
    enabled: true
    severity: low
    config:
      blocked_keywords: []
""",
    "basic": """\
# Basic governance policy
name: basic-policy
version: "1.0"
rules:
  - type: pii_check
    enabled: true
    severity: high
  - type: keyword_block
    enabled: true
    severity: medium
    config:
      blocked_keywords:
        - "DROP TABLE"
        - "DELETE FROM"
        - "rm -rf"
""",
    "full": """\
# Full governance policy
name: full-policy
version: "1.0"
rules:
  - type: pii_check
    enabled: true
    severity: critical
  - type: role_check
    enabled: true
    severity: high
    config:
      allowed_roles:
        - admin
        - operator
        - auditor
  - type: cost_limit
    enabled: true
    severity: medium
    config:
      max_cost_per_action: 1.0
      max_cost_per_session: 10.0
  - type: keyword_block
    enabled: true
    severity: medium
    config:
      blocked_keywords:
        - "DROP TABLE"
        - "DELETE FROM"
        - "TRUNCATE"
        - "rm -rf"
        - "sudo"
""",
}


def get_template(name: str) -> str:
    """Return the YAML source for a built-in policy template.

    Parameters
    ----------
    name:
        Template name.  Use :func:`list_templates` to discover available names.

    Returns
    -------
    str
        YAML-formatted policy template string.

    Raises
    ------
    KeyError
        If ``name`` is not a recognised built-in template.
    """
    if name not in TEMPLATES:
        available = list_templates()
        raise KeyError(
            f"Unknown template: {name!r}. Available templates: {available}"
        )
    return TEMPLATES[name]


def list_templates() -> list[str]:
    """Return the names of all available built-in policy templates.

    Returns
    -------
    list[str]
        Alphabetically sorted list of template names.
    """
    return sorted(TEMPLATES.keys())


def write_template(name: str, output_path: Path) -> Path:
    """Write a built-in policy template to ``output_path``.

    Parent directories are created automatically if they do not exist.

    Parameters
    ----------
    name:
        Template name, as returned by :func:`list_templates`.
    output_path:
        Destination file path (typically ending in ``.yaml``).

    Returns
    -------
    Path
        The resolved path of the written file.

    Raises
    ------
    KeyError
        If ``name`` is not a recognised built-in template.
    """
    content = get_template(name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path

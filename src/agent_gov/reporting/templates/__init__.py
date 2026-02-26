"""Jinja2 template helpers for the reporting subsystem.

Provides utilities for listing, loading, and writing the built-in Jinja2
report templates.  Templates live in the same directory as this module.

Built-in templates
------------------
- ``governance_report.md.j2`` — Markdown governance/audit report
- ``compliance_report.md.j2`` — Markdown compliance framework report
"""
from __future__ import annotations

from pathlib import Path

_TEMPLATES_DIR = Path(__file__).parent

_BUILTIN_TEMPLATES: tuple[str, ...] = (
    "governance_report.md.j2",
    "compliance_report.md.j2",
)


def list_templates() -> list[str]:
    """Return the names of all built-in Jinja2 templates.

    Returns
    -------
    list[str]
        Sorted list of template file names available in this package.
    """
    return sorted(
        p.name
        for p in _TEMPLATES_DIR.iterdir()
        if p.suffix in (".j2", ".jinja2") and p.is_file()
    )


def get_template(name: str) -> str:
    """Return the raw text content of a built-in template.

    Parameters
    ----------
    name:
        Template file name (e.g. ``"governance_report.md.j2"``).

    Returns
    -------
    str
        Raw template text.

    Raises
    ------
    FileNotFoundError
        If no template with ``name`` exists in the templates directory.
    """
    template_path = _TEMPLATES_DIR / name
    if not template_path.is_file():
        available = list_templates()
        raise FileNotFoundError(
            f"Template {name!r} not found. Available templates: {available!r}"
        )
    return template_path.read_text(encoding="utf-8")


def write_template(name: str, destination: str | Path) -> Path:
    """Copy a built-in template to a destination path.

    Useful for scaffolding custom templates that extend the built-ins.

    Parameters
    ----------
    name:
        Template file name to copy.
    destination:
        Destination file path.  Parent directories are created if needed.

    Returns
    -------
    Path
        Resolved path of the written file.

    Raises
    ------
    FileNotFoundError
        If the named template does not exist.
    """
    content = get_template(name)
    resolved = Path(destination).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return resolved

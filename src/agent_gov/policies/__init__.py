"""Policy-as-Code library for agent governance.

This sub-package provides a curated library of governance policy files
organized by compliance domain, along with tools to discover, load,
validate, and install those policy files.

Public surface
--------------
- :class:`LibraryPolicyLoader` — discovers and loads library YAML policies
- :class:`LibraryPolicyValidator` — validates policy YAML against the library schema
- :class:`LibraryPolicyInstaller` — copies policies to a target directory
- :exc:`LibraryPolicyLoadError` — raised on load failures
- :exc:`LibraryPolicyValidationError` — raised on schema validation failures
"""
from __future__ import annotations

from agent_gov.policies.loader import LibraryPolicyLoadError, LibraryPolicyLoader
from agent_gov.policies.validator import LibraryPolicyValidationError, LibraryPolicyValidator
from agent_gov.policies.installer import LibraryPolicyInstaller

__all__ = [
    "LibraryPolicyInstaller",
    "LibraryPolicyLoadError",
    "LibraryPolicyLoader",
    "LibraryPolicyValidationError",
    "LibraryPolicyValidator",
]

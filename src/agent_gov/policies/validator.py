"""Library policy YAML validator.

Provides :class:`LibraryPolicyValidator` for validating raw YAML data or
:class:`~agent_gov.policies.schema.LibraryPolicyConfig` objects against the
library policy schema.  The validator checks required fields, allowed enum
values, and structural constraints beyond what Pydantic enforces automatically.

Example::

    from agent_gov.policies.validator import LibraryPolicyValidator

    validator = LibraryPolicyValidator()
    errors = validator.validate_dict({"id": "my-policy", "name": "Test"})
    if errors:
        for error in errors:
            print(error)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from agent_gov.policies.schema import (
    LibraryDomain,
    LibraryPolicyConfig,
    LibrarySeverity,
)

_REQUIRED_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "version",
    "domain",
    "rules",
)

_REQUIRED_RULE_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "condition",
    "action",
    "message",
)

_VALID_DOMAINS: frozenset[str] = frozenset(d.value for d in LibraryDomain)
_VALID_SEVERITIES: frozenset[str] = frozenset(s.value for s in LibrarySeverity)


class LibraryPolicyValidationError(Exception):
    """Raised when a policy fails schema validation.

    Attributes
    ----------
    errors:
        List of human-readable error messages describing each violation.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        summary = "; ".join(errors)
        super().__init__(f"Policy validation failed: {summary}")


@dataclass
class ValidationResult:
    """Result of validating a single policy document.

    Attributes
    ----------
    valid:
        ``True`` when no errors were found.
    errors:
        List of human-readable error strings.  Empty when ``valid`` is ``True``.
    """

    valid: bool
    errors: list[str] = field(default_factory=list)


class LibraryPolicyValidator:
    """Validates library governance policy YAML against the library schema.

    Validation checks performed:

    * Required top-level fields are present: ``id``, ``name``, ``version``,
      ``domain``, ``rules``.
    * ``domain`` is a valid :class:`~agent_gov.policies.schema.LibraryDomain`
      value.
    * ``severity`` (if present) is a valid
      :class:`~agent_gov.policies.schema.LibrarySeverity` value.
    * Each rule has the required fields: ``id``, ``name``, ``condition``,
      ``action``, ``message``.
    * Full Pydantic model validation via
      :class:`~agent_gov.policies.schema.LibraryPolicyConfig`.
    """

    def validate_dict(self, data: object) -> ValidationResult:
        """Validate a raw Python object (from YAML parsing) against the schema.

        Parameters
        ----------
        data:
            The parsed YAML document, expected to be a ``dict``.

        Returns
        -------
        ValidationResult
            Contains ``valid=True`` with no errors, or ``valid=False``
            with a populated ``errors`` list.
        """
        errors: list[str] = []

        if not isinstance(data, dict):
            return ValidationResult(valid=False, errors=["Policy document must be a YAML mapping (dict)."])

        # Required top-level fields
        for required_field in _REQUIRED_TOP_LEVEL_FIELDS:
            if required_field not in data:
                errors.append(f"Missing required field: '{required_field}'.")

        # Domain validation
        domain_value = data.get("domain")
        if domain_value is not None and domain_value not in _VALID_DOMAINS:
            errors.append(
                f"Invalid domain '{domain_value}'. "
                f"Must be one of: {sorted(_VALID_DOMAINS)}."
            )

        # Severity validation
        severity_value = data.get("severity")
        if severity_value is not None and severity_value not in _VALID_SEVERITIES:
            errors.append(
                f"Invalid severity '{severity_value}'. "
                f"Must be one of: {sorted(_VALID_SEVERITIES)}."
            )

        # Rules validation
        rules = data.get("rules")
        if rules is not None:
            if not isinstance(rules, list):
                errors.append("'rules' must be a list.")
            else:
                for index, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        errors.append(f"Rule at index {index} must be a mapping (dict).")
                        continue
                    for required_rule_field in _REQUIRED_RULE_FIELDS:
                        if required_rule_field not in rule:
                            rule_id = rule.get("id", f"<index {index}>")
                            errors.append(
                                f"Rule '{rule_id}' is missing required field: '{required_rule_field}'."
                            )

        if errors:
            return ValidationResult(valid=False, errors=errors)

        # Full Pydantic validation
        try:
            LibraryPolicyConfig.model_validate(data)
        except Exception as exc:
            return ValidationResult(valid=False, errors=[f"Schema validation error: {exc}"])

        return ValidationResult(valid=True)

    def validate_file(self, path: str | Path) -> ValidationResult:
        """Validate a YAML policy file on disk.

        Parameters
        ----------
        path:
            Filesystem path to the ``.yaml`` or ``.yml`` policy file.

        Returns
        -------
        ValidationResult
            Contains ``valid=True`` with no errors, or ``valid=False``
            with a populated ``errors`` list describing each problem.
        """
        resolved = Path(path).resolve()

        if not resolved.exists():
            return ValidationResult(
                valid=False, errors=[f"File does not exist: {resolved}"]
            )
        if not resolved.is_file():
            return ValidationResult(
                valid=False, errors=[f"Path is not a file: {resolved}"]
            )

        try:
            raw_text = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            return ValidationResult(
                valid=False, errors=[f"Cannot read file '{resolved}': {exc}"]
            )

        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            return ValidationResult(
                valid=False, errors=[f"YAML parse error: {exc}"]
            )

        return self.validate_dict(data)

    def assert_valid(self, data: object) -> LibraryPolicyConfig:
        """Validate and return the parsed policy, raising on failure.

        Parameters
        ----------
        data:
            The parsed YAML document as a Python ``dict``.

        Returns
        -------
        LibraryPolicyConfig
            The validated policy model.

        Raises
        ------
        LibraryPolicyValidationError
            If validation fails.
        """
        result = self.validate_dict(data)
        if not result.valid:
            raise LibraryPolicyValidationError(result.errors)
        return LibraryPolicyConfig.model_validate(data)

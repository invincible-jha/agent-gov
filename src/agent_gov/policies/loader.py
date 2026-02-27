"""Library policy loader — discovers and loads YAML governance policies.

Provides :class:`LibraryPolicyLoader` for loading individual policy files or
recursively scanning a directory tree to load all policies found within it.

The loader validates each file against :class:`~agent_gov.policies.schema.LibraryPolicyConfig`
using Pydantic v2. Files that fail to parse or validate are skipped with a
warning rather than aborting the scan, making bulk loading resilient.

Example — load a single file::

    from agent_gov.policies.loader import LibraryPolicyLoader

    loader = LibraryPolicyLoader()
    policy = loader.load_file("/path/to/policies/healthcare/hipaa_phi_protection.yaml")

Example — load a whole directory::

    policies = loader.load_directory("/path/to/policies/", recursive=True)
    for policy in policies:
        print(policy.id, policy.domain, policy.severity)
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from agent_gov.policies.schema import LibraryPolicyConfig

logger = logging.getLogger(__name__)

_YAML_EXTENSIONS: frozenset[str] = frozenset({".yaml", ".yml"})


class LibraryPolicyLoadError(Exception):
    """Raised when a library policy file cannot be parsed or validated.

    Attributes
    ----------
    path:
        The filesystem path that triggered the error.
    reason:
        Human-readable explanation of the failure.
    """

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load library policy from {path!s}: {reason}")


class LibraryPolicyLoader:
    """Loads :class:`~agent_gov.policies.schema.LibraryPolicyConfig` from YAML sources.

    The loader is stateless — each call produces fresh objects without caching.
    Files that fail validation during directory scans are logged and skipped
    rather than raising, allowing a partially-valid directory to be consumed.
    """

    def load_file(self, path: str | Path) -> LibraryPolicyConfig:
        """Load a single library policy YAML file.

        Parameters
        ----------
        path:
            Filesystem path to the ``.yaml`` or ``.yml`` file.

        Returns
        -------
        LibraryPolicyConfig
            Validated library policy configuration.

        Raises
        ------
        LibraryPolicyLoadError
            If the file does not exist, is not valid YAML, or fails
            Pydantic schema validation.
        """
        resolved = Path(path).resolve()
        if not resolved.exists():
            raise LibraryPolicyLoadError(resolved, "file does not exist")
        if not resolved.is_file():
            raise LibraryPolicyLoadError(resolved, "path is not a file")

        try:
            raw_text = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            raise LibraryPolicyLoadError(resolved, f"cannot read file: {exc}") from exc

        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise LibraryPolicyLoadError(resolved, f"YAML parse error: {exc}") from exc

        if not isinstance(data, dict):
            raise LibraryPolicyLoadError(resolved, "YAML root must be a mapping (dict)")

        try:
            policy = LibraryPolicyConfig.model_validate(data)
        except Exception as exc:
            raise LibraryPolicyLoadError(
                resolved, f"schema validation failed: {exc}"
            ) from exc

        logger.debug("Loaded library policy %r from %s", policy.id, resolved)
        return policy

    def load_directory(
        self,
        directory: str | Path,
        *,
        recursive: bool = True,
        domain_filter: str | None = None,
    ) -> list[LibraryPolicyConfig]:
        """Load all library YAML policy files from a directory.

        Parameters
        ----------
        directory:
            Path to a directory containing ``.yaml`` / ``.yml`` policy files.
        recursive:
            When ``True`` (default), scan subdirectories as well.  Set to
            ``False`` to scan only the top-level directory.
        domain_filter:
            When provided, only policies whose ``domain`` value matches this
            string are returned.

        Returns
        -------
        list[LibraryPolicyConfig]
            All successfully validated policies, sorted by file path.
            Individual file failures are logged as warnings and skipped.

        Raises
        ------
        LibraryPolicyLoadError
            If ``directory`` does not exist or is not a directory.
        """
        resolved = Path(directory).resolve()
        if not resolved.exists():
            raise LibraryPolicyLoadError(resolved, "directory does not exist")
        if not resolved.is_dir():
            raise LibraryPolicyLoadError(resolved, "path is not a directory")

        glob_pattern = "**/*" if recursive else "*"
        candidates = sorted(resolved.glob(glob_pattern))

        policies: list[LibraryPolicyConfig] = []
        for candidate in candidates:
            if candidate.suffix.lower() not in _YAML_EXTENSIONS:
                continue
            if not candidate.is_file():
                continue
            try:
                policy = self.load_file(candidate)
            except LibraryPolicyLoadError as exc:
                logger.warning("Skipping %s: %s", candidate, exc.reason)
                continue

            if domain_filter is not None and policy.domain.value != domain_filter:
                continue

            policies.append(policy)

        logger.debug(
            "Loaded %d library policies from %s (recursive=%s, domain_filter=%r)",
            len(policies),
            resolved,
            recursive,
            domain_filter,
        )
        return policies

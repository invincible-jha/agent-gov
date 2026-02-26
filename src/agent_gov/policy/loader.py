"""YAML policy loader — single-file and directory-based loading.

Supports loading a single ``.yaml`` / ``.yml`` policy file or scanning an
entire directory and merging all policies found into a list.

Example
-------
Load a single policy::

    from agent_gov.policy.loader import PolicyLoader

    loader = PolicyLoader()
    policy = loader.load_file("/path/to/policy.yaml")

Load all policies in a directory::

    policies = loader.load_directory("/path/to/policies/")
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from agent_gov.policy.schema import PolicyConfig

logger = logging.getLogger(__name__)

_YAML_EXTENSIONS: frozenset[str] = frozenset({".yaml", ".yml"})


class PolicyLoadError(Exception):
    """Raised when a policy file cannot be parsed or validated."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load policy from {path!s}: {reason}")


class PolicyLoader:
    """Loads :class:`~agent_gov.policy.schema.PolicyConfig` from YAML sources.

    The loader is stateless — each call produces fresh objects without caching.
    """

    def load_file(self, path: str | Path) -> PolicyConfig:
        """Load a single YAML policy file.

        Parameters
        ----------
        path:
            Filesystem path to the ``.yaml`` or ``.yml`` file.

        Returns
        -------
        PolicyConfig
            Validated policy configuration.

        Raises
        ------
        PolicyLoadError
            If the file does not exist, is not valid YAML, or fails
            Pydantic validation.
        """
        resolved = Path(path).resolve()
        if not resolved.exists():
            raise PolicyLoadError(resolved, "file does not exist")
        if not resolved.is_file():
            raise PolicyLoadError(resolved, "path is not a file")

        try:
            raw_text = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            raise PolicyLoadError(resolved, f"cannot read file: {exc}") from exc

        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise PolicyLoadError(resolved, f"YAML parse error: {exc}") from exc

        if not isinstance(data, dict):
            raise PolicyLoadError(resolved, "YAML root must be a mapping (dict)")

        try:
            policy = PolicyConfig.model_validate(data)
        except Exception as exc:
            raise PolicyLoadError(resolved, f"schema validation failed: {exc}") from exc

        logger.debug("Loaded policy %r from %s", policy.name, resolved)
        return policy

    def load_directory(
        self,
        directory: str | Path,
        *,
        recursive: bool = False,
    ) -> list[PolicyConfig]:
        """Load all YAML policy files from a directory.

        Parameters
        ----------
        directory:
            Path to a directory containing ``.yaml`` / ``.yml`` files.
        recursive:
            When ``True``, scan subdirectories as well.

        Returns
        -------
        list[PolicyConfig]
            All successfully validated policies, sorted by filename.

        Raises
        ------
        PolicyLoadError
            If ``directory`` does not exist or is not a directory.
            Individual file failures are logged as warnings and skipped.
        """
        resolved = Path(directory).resolve()
        if not resolved.exists():
            raise PolicyLoadError(resolved, "directory does not exist")
        if not resolved.is_dir():
            raise PolicyLoadError(resolved, "path is not a directory")

        glob_pattern = "**/*" if recursive else "*"
        candidates = sorted(resolved.glob(glob_pattern))

        policies: list[PolicyConfig] = []
        for candidate in candidates:
            if candidate.suffix.lower() not in _YAML_EXTENSIONS:
                continue
            if not candidate.is_file():
                continue
            try:
                policy = self.load_file(candidate)
                policies.append(policy)
            except PolicyLoadError as exc:
                logger.warning("Skipping %s: %s", candidate, exc.reason)

        logger.debug(
            "Loaded %d policies from directory %s", len(policies), resolved
        )
        return policies

    def load_string(self, content: str, *, source_name: str = "<string>") -> PolicyConfig:
        """Load a policy from a YAML string.

        Useful for testing or loading policies from configuration stores.

        Parameters
        ----------
        content:
            Raw YAML text.
        source_name:
            Logical name used in error messages.

        Returns
        -------
        PolicyConfig
            Validated policy configuration.

        Raises
        ------
        PolicyLoadError
            If the content is not valid YAML or fails schema validation.
        """
        fake_path = Path(source_name)
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise PolicyLoadError(fake_path, f"YAML parse error: {exc}") from exc

        if not isinstance(data, dict):
            raise PolicyLoadError(fake_path, "YAML root must be a mapping (dict)")

        try:
            policy = PolicyConfig.model_validate(data)
        except Exception as exc:
            raise PolicyLoadError(fake_path, f"schema validation failed: {exc}") from exc

        return policy

"""Library policy installer — copies governance policies to a target directory.

Provides :class:`LibraryPolicyInstaller` for installing policies from a source
directory (e.g. the built-in ``policies/`` library) into a project's working
directory.  Supports filtering by domain and dry-run preview mode.

Example — install all policies::

    from agent_gov.policies.installer import LibraryPolicyInstaller

    installer = LibraryPolicyInstaller()
    results = installer.install(
        source="/path/to/policies/",
        target="/my-project/policies/",
    )
    for result in results:
        print(result.source_path, "->", result.target_path)

Example — install only healthcare policies::

    results = installer.install(
        source="/path/to/policies/",
        target="/my-project/policies/",
        domain="healthcare",
    )
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agent_gov.policies.loader import LibraryPolicyLoadError, LibraryPolicyLoader

_YAML_EXTENSIONS: frozenset[str] = frozenset({".yaml", ".yml"})


@dataclass
class InstallResult:
    """Result entry for a single policy file installation.

    Attributes
    ----------
    source_path:
        Absolute path of the source policy file.
    target_path:
        Absolute path of the destination policy file.
    policy_id:
        The ``id`` field from the installed policy.
    domain:
        The ``domain`` field from the installed policy.
    skipped:
        ``True`` if the file was skipped (e.g. filtered out or dry-run).
    dry_run:
        ``True`` if this result represents a dry-run preview (no file written).
    error:
        Non-empty string if installation failed for this file.
    """

    source_path: Path
    target_path: Path
    policy_id: str
    domain: str
    skipped: bool = False
    dry_run: bool = False
    error: str = ""

    @property
    def success(self) -> bool:
        """Return ``True`` when the file was installed without error."""
        return not self.skipped and not self.error


class LibraryPolicyInstaller:
    """Copies library governance policy YAML files to a target directory.

    The installer uses :class:`~agent_gov.policies.loader.LibraryPolicyLoader`
    to discover and validate each source policy before copying.  Policies that
    fail validation are recorded with an error in their :class:`InstallResult`
    rather than aborting the entire install.
    """

    def __init__(self) -> None:
        self._loader = LibraryPolicyLoader()

    def install(
        self,
        source: str | Path,
        target: str | Path,
        *,
        domain: Optional[str] = None,
        overwrite: bool = True,
        dry_run: bool = False,
    ) -> list[InstallResult]:
        """Install policies from *source* into *target*.

        Parameters
        ----------
        source:
            Directory containing source ``.yaml`` policy files.  Scanned
            recursively.
        target:
            Destination directory.  Created if it does not exist (unless
            ``dry_run`` is ``True``).
        domain:
            When provided, only install policies whose ``domain`` matches.
        overwrite:
            When ``False``, skip files that already exist in *target*.
        dry_run:
            When ``True``, report what would be installed without writing any
            files or creating directories.

        Returns
        -------
        list[InstallResult]
            One entry per discovered YAML file.
        """
        source_path = Path(source).resolve()
        target_path = Path(target).resolve()

        if not source_path.exists():
            raise ValueError(f"Source directory does not exist: {source_path}")
        if not source_path.is_dir():
            raise ValueError(f"Source path is not a directory: {source_path}")

        if not dry_run:
            target_path.mkdir(parents=True, exist_ok=True)

        results: list[InstallResult] = []

        for candidate in sorted(source_path.rglob("*")):
            if candidate.suffix.lower() not in _YAML_EXTENSIONS:
                continue
            if not candidate.is_file():
                continue

            # Load and validate
            try:
                policy = self._loader.load_file(candidate)
            except LibraryPolicyLoadError as exc:
                relative = candidate.relative_to(source_path)
                dest = target_path / relative
                results.append(
                    InstallResult(
                        source_path=candidate,
                        target_path=dest,
                        policy_id="<unknown>",
                        domain="<unknown>",
                        error=str(exc.reason),
                    )
                )
                continue

            # Domain filter
            if domain is not None and policy.domain.value != domain:
                relative = candidate.relative_to(source_path)
                dest = target_path / relative
                results.append(
                    InstallResult(
                        source_path=candidate,
                        target_path=dest,
                        policy_id=policy.id,
                        domain=policy.domain.value,
                        skipped=True,
                        dry_run=dry_run,
                    )
                )
                continue

            # Compute destination preserving sub-directory structure
            relative = candidate.relative_to(source_path)
            dest = target_path / relative

            # Overwrite check
            if not overwrite and dest.exists():
                results.append(
                    InstallResult(
                        source_path=candidate,
                        target_path=dest,
                        policy_id=policy.id,
                        domain=policy.domain.value,
                        skipped=True,
                        dry_run=dry_run,
                    )
                )
                continue

            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(candidate), str(dest))

            results.append(
                InstallResult(
                    source_path=candidate,
                    target_path=dest,
                    policy_id=policy.id,
                    domain=policy.domain.value,
                    dry_run=dry_run,
                )
            )

        return results

    def list_available(
        self,
        source: str | Path,
        *,
        domain: Optional[str] = None,
    ) -> list[str]:
        """List policy IDs available in the source directory.

        Parameters
        ----------
        source:
            Directory to scan for policy YAML files.
        domain:
            When provided, only return IDs for the given domain.

        Returns
        -------
        list[str]
            Sorted list of policy ``id`` values found.
        """
        try:
            policies = self._loader.load_directory(
                source, recursive=True, domain_filter=domain
            )
        except LibraryPolicyLoadError:
            return []
        return sorted(policy.id for policy in policies)

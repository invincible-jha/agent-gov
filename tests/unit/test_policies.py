"""Unit tests for the agent_gov.policies package.

Covers:
- LibraryPolicyLoader: load_file, load_directory, domain filtering
- LibraryPolicyValidator: validate_dict, validate_file, assert_valid
- LibraryPolicyInstaller: install, dry_run, domain filter, overwrite behaviour
- CLI commands: policy list, policy install, policy validate
- All 20 bundled library policy files parse successfully
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Optional

import pytest
import yaml
from click.testing import CliRunner

from agent_gov.policies.installer import InstallResult, LibraryPolicyInstaller
from agent_gov.policies.loader import LibraryPolicyLoadError, LibraryPolicyLoader
from agent_gov.policies.schema import (
    LibraryDomain,
    LibraryPolicyConfig,
    LibraryRuleAction,
    LibrarySeverity,
)
from agent_gov.policies.validator import (
    LibraryPolicyValidationError,
    LibraryPolicyValidator,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Helpers — canonical policy YAML strings
# ---------------------------------------------------------------------------

_VALID_POLICY_YAML = textwrap.dedent("""\
    id: test-policy-001
    name: Test Policy
    version: "1.0"
    domain: general
    description: |
      A minimal valid policy used in tests.
    severity: medium
    rules:
      - id: rule-001
        name: Block Bad Keyword
        condition: keyword_block
        parameters:
          keywords:
            - "bad word"
          target: input
          case_sensitive: false
        action: block
        message: "Bad keyword detected."
    references:
      - "https://example.com/policy"
    tags:
      - test
      - general
""")

_VALID_HEALTHCARE_POLICY_YAML = textwrap.dedent("""\
    id: test-hipaa-001
    name: Test HIPAA Policy
    version: "1.0"
    domain: healthcare
    description: A healthcare test policy.
    severity: critical
    rules:
      - id: phi-001
        name: Block PHI
        condition: regex_match
        parameters:
          pattern: "\\\\bSSN\\\\b"
          target: output
        action: redact
        message: "PHI detected."
    references: []
    tags:
      - hipaa
""")

_VALID_GDPR_POLICY_YAML = textwrap.dedent("""\
    id: test-gdpr-001
    name: Test GDPR Policy
    version: "1.0"
    domain: gdpr
    description: A GDPR test policy.
    severity: high
    rules:
      - id: gdpr-001
        name: Require Consent
        condition: keyword_block
        parameters:
          keywords:
            - "process personal data"
          require_field: consent_id
          case_sensitive: false
          target: input
        action: warn
        message: "Consent ID required."
    references:
      - "https://gdpr-info.eu/"
    tags:
      - gdpr
      - consent
""")

_MISSING_ID_YAML = textwrap.dedent("""\
    name: Missing ID Policy
    version: "1.0"
    domain: general
    severity: low
    rules: []
""")

_MISSING_NAME_YAML = textwrap.dedent("""\
    id: missing-name-policy
    version: "1.0"
    domain: general
    severity: low
    rules: []
""")

_INVALID_DOMAIN_YAML = textwrap.dedent("""\
    id: bad-domain-policy
    name: Bad Domain Policy
    version: "1.0"
    domain: unknown-domain
    severity: medium
    rules: []
""")

_INVALID_SEVERITY_YAML = textwrap.dedent("""\
    id: bad-severity-policy
    name: Bad Severity Policy
    version: "1.0"
    domain: general
    severity: extreme
    rules: []
""")

_RULE_MISSING_ID_YAML = textwrap.dedent("""\
    id: rule-missing-id
    name: Rule Missing ID
    version: "1.0"
    domain: general
    severity: low
    rules:
      - name: Some Rule
        condition: keyword_block
        parameters: {}
        action: warn
        message: "Missing id field."
""")

_RULE_MISSING_ACTION_YAML = textwrap.dedent("""\
    id: rule-missing-action
    name: Rule Missing Action
    version: "1.0"
    domain: general
    severity: low
    rules:
      - id: r-001
        name: Some Rule
        condition: keyword_block
        parameters: {}
        message: "Missing action field."
""")

_NON_DICT_YAML = "- item1\n- item2\n"
_INVALID_YAML = "key: [unclosed bracket"


# ---------------------------------------------------------------------------
# Path to the built-in policies directory
# ---------------------------------------------------------------------------

def _policies_dir() -> Path:
    """Return the absolute path to the repository's policies/ directory."""
    # src/agent_gov/policies/ -> src/agent_gov/ -> src/ -> repo_root/
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent
    return repo_root / "policies"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_policy_file(tmp_path: Path) -> Path:
    policy_file = tmp_path / "test_policy.yaml"
    policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
    return policy_file


@pytest.fixture()
def multi_domain_policy_dir(tmp_path: Path) -> Path:
    """A directory with policies from multiple domains."""
    (tmp_path / "healthcare").mkdir()
    (tmp_path / "general").mkdir()

    (tmp_path / "healthcare" / "hipaa.yaml").write_text(
        _VALID_HEALTHCARE_POLICY_YAML, encoding="utf-8"
    )
    (tmp_path / "general" / "keywords.yaml").write_text(
        _VALID_POLICY_YAML, encoding="utf-8"
    )
    return tmp_path


# ===========================================================================
# LibraryPolicyLoader tests
# ===========================================================================

class TestLibraryPolicyLoaderLoadFile:
    def test_load_valid_yaml_file(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(policy_file)
        assert isinstance(policy, LibraryPolicyConfig)
        assert policy.id == "test-policy-001"

    def test_load_returns_correct_name(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(policy_file)
        assert policy.name == "Test Policy"

    def test_load_returns_correct_domain(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(policy_file)
        assert policy.domain == LibraryDomain.GENERAL

    def test_load_returns_correct_severity(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(policy_file)
        assert policy.severity == LibrarySeverity.MEDIUM

    def test_load_parses_rules(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(policy_file)
        assert len(policy.rules) == 1
        assert policy.rules[0].id == "rule-001"
        assert policy.rules[0].action == LibraryRuleAction.BLOCK

    def test_load_accepts_string_path(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(str(policy_file))
        assert policy.id == "test-policy-001"

    def test_load_accepts_yml_extension(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policy = loader.load_file(policy_file)
        assert policy.id == "test-policy-001"

    def test_missing_file_raises_load_error(self, tmp_path: Path) -> None:
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError) as exc_info:
            loader.load_file(tmp_path / "nonexistent.yaml")
        assert "does not exist" in str(exc_info.value)

    def test_directory_path_raises_load_error(self, tmp_path: Path) -> None:
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError) as exc_info:
            loader.load_file(tmp_path)
        assert "not a file" in str(exc_info.value)

    def test_invalid_yaml_raises_load_error(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "bad.yaml"
        policy_file.write_text(_INVALID_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError) as exc_info:
            loader.load_file(policy_file)
        assert "YAML parse error" in str(exc_info.value)

    def test_non_dict_yaml_raises_load_error(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "list.yaml"
        policy_file.write_text(_NON_DICT_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError) as exc_info:
            loader.load_file(policy_file)
        assert "mapping" in str(exc_info.value).lower()

    def test_schema_validation_failure_raises(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "bad_schema.yaml"
        policy_file.write_text(_INVALID_DOMAIN_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError) as exc_info:
            loader.load_file(policy_file)
        assert "schema validation failed" in str(exc_info.value)

    def test_load_error_has_path_attribute(self, tmp_path: Path) -> None:
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError) as exc_info:
            loader.load_file(tmp_path / "ghost.yaml")
        assert exc_info.value.path is not None


class TestLibraryPolicyLoaderLoadDirectory:
    def test_loads_single_file(self, tmp_path: Path) -> None:
        (tmp_path / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 1

    def test_loads_multiple_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (tmp_path / "b.yaml").write_text(_VALID_HEALTHCARE_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 2

    def test_ignores_non_yaml_files(self, tmp_path: Path) -> None:
        (tmp_path / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (tmp_path / "readme.txt").write_text("not yaml", encoding="utf-8")
        (tmp_path / "data.json").write_text("{}", encoding="utf-8")
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 1

    def test_skips_invalid_files_without_raising(self, tmp_path: Path) -> None:
        (tmp_path / "valid.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (tmp_path / "invalid.yaml").write_text(_INVALID_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 1
        assert policies[0].id == "test-policy-001"

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert policies == []

    def test_missing_directory_raises(self, tmp_path: Path) -> None:
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError):
            loader.load_directory(tmp_path / "no-such-dir")

    def test_file_path_as_directory_raises(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        loader = LibraryPolicyLoader()
        with pytest.raises(LibraryPolicyLoadError):
            loader.load_directory(policy_file)

    def test_recursive_loads_subdirectories(self, multi_domain_policy_dir: Path) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(multi_domain_policy_dir, recursive=True)
        assert len(policies) == 2

    def test_non_recursive_misses_subdirectories(self, multi_domain_policy_dir: Path) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(multi_domain_policy_dir, recursive=False)
        assert len(policies) == 0

    def test_domain_filter_returns_only_matching(self, multi_domain_policy_dir: Path) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            multi_domain_policy_dir,
            recursive=True,
            domain_filter="healthcare",
        )
        assert len(policies) == 1
        assert policies[0].domain == LibraryDomain.HEALTHCARE

    def test_domain_filter_returns_empty_for_no_match(self, multi_domain_policy_dir: Path) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            multi_domain_policy_dir,
            recursive=True,
            domain_filter="finance",
        )
        assert policies == []


# ===========================================================================
# LibraryPolicyValidator tests
# ===========================================================================

class TestLibraryPolicyValidatorDict:
    def test_valid_dict_returns_valid(self) -> None:
        data = yaml.safe_load(_VALID_POLICY_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is True
        assert result.errors == []

    def test_missing_id_returns_error(self) -> None:
        data = yaml.safe_load(_MISSING_ID_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("id" in err for err in result.errors)

    def test_missing_name_returns_error(self) -> None:
        data = yaml.safe_load(_MISSING_NAME_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("name" in err for err in result.errors)

    def test_invalid_domain_returns_error(self) -> None:
        data = yaml.safe_load(_INVALID_DOMAIN_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("domain" in err.lower() for err in result.errors)

    def test_invalid_severity_returns_error(self) -> None:
        data = yaml.safe_load(_INVALID_SEVERITY_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("severity" in err.lower() for err in result.errors)

    def test_non_dict_returns_error(self) -> None:
        data = yaml.safe_load(_NON_DICT_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_rule_missing_id_returns_error(self) -> None:
        data = yaml.safe_load(_RULE_MISSING_ID_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("id" in err for err in result.errors)

    def test_rule_missing_action_returns_error(self) -> None:
        data = yaml.safe_load(_RULE_MISSING_ACTION_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("action" in err for err in result.errors)

    def test_valid_healthcare_policy(self) -> None:
        data = yaml.safe_load(_VALID_HEALTHCARE_POLICY_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is True

    def test_valid_gdpr_policy(self) -> None:
        data = yaml.safe_load(_VALID_GDPR_POLICY_YAML)
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is True

    def test_missing_rules_field_returns_error(self) -> None:
        data: dict[str, object] = {
            "id": "no-rules",
            "name": "No Rules Policy",
            "version": "1.0",
            "domain": "general",
            "severity": "low",
        }
        validator = LibraryPolicyValidator()
        result = validator.validate_dict(data)
        assert result.valid is False
        assert any("rules" in err for err in result.errors)


class TestLibraryPolicyValidatorFile:
    def test_validate_valid_file(self, valid_policy_file: Path) -> None:
        validator = LibraryPolicyValidator()
        result = validator.validate_file(valid_policy_file)
        assert result.valid is True

    def test_validate_missing_file(self, tmp_path: Path) -> None:
        validator = LibraryPolicyValidator()
        result = validator.validate_file(tmp_path / "nonexistent.yaml")
        assert result.valid is False
        assert any("does not exist" in err for err in result.errors)

    def test_validate_invalid_yaml_file(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(_INVALID_YAML, encoding="utf-8")
        validator = LibraryPolicyValidator()
        result = validator.validate_file(bad_file)
        assert result.valid is False
        assert any("parse error" in err.lower() for err in result.errors)

    def test_validate_invalid_schema_file(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad_schema.yaml"
        bad_file.write_text(_MISSING_ID_YAML, encoding="utf-8")
        validator = LibraryPolicyValidator()
        result = validator.validate_file(bad_file)
        assert result.valid is False

    def test_validate_directory_path_returns_error(self, tmp_path: Path) -> None:
        validator = LibraryPolicyValidator()
        result = validator.validate_file(tmp_path)
        assert result.valid is False
        assert any("not a file" in err for err in result.errors)


class TestLibraryPolicyValidatorAssertValid:
    def test_assert_valid_returns_model_on_success(self) -> None:
        data = yaml.safe_load(_VALID_POLICY_YAML)
        validator = LibraryPolicyValidator()
        policy = validator.assert_valid(data)
        assert isinstance(policy, LibraryPolicyConfig)
        assert policy.id == "test-policy-001"

    def test_assert_valid_raises_on_missing_field(self) -> None:
        data = yaml.safe_load(_MISSING_ID_YAML)
        validator = LibraryPolicyValidator()
        with pytest.raises(LibraryPolicyValidationError) as exc_info:
            validator.assert_valid(data)
        assert exc_info.value.errors

    def test_assert_valid_raises_on_invalid_domain(self) -> None:
        data = yaml.safe_load(_INVALID_DOMAIN_YAML)
        validator = LibraryPolicyValidator()
        with pytest.raises(LibraryPolicyValidationError):
            validator.assert_valid(data)

    def test_validation_error_has_errors_attribute(self) -> None:
        data = yaml.safe_load(_INVALID_SEVERITY_YAML)
        validator = LibraryPolicyValidator()
        with pytest.raises(LibraryPolicyValidationError) as exc_info:
            validator.assert_valid(data)
        assert isinstance(exc_info.value.errors, list)
        assert len(exc_info.value.errors) > 0


# ===========================================================================
# LibraryPolicyInstaller tests
# ===========================================================================

class TestLibraryPolicyInstaller:
    def test_install_copies_file_to_target(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")

        installer = LibraryPolicyInstaller()
        results = installer.install(source=source, target=target)

        assert len(results) == 1
        assert results[0].success is True
        assert (target / "policy.yaml").exists()

    def test_install_creates_target_directory(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "new" / "nested" / "target"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")

        installer = LibraryPolicyInstaller()
        installer.install(source=source, target=target)

        assert target.exists()

    def test_install_preserves_subdirectory_structure(self, multi_domain_policy_dir: Path, tmp_path: Path) -> None:
        target = tmp_path / "installed"
        installer = LibraryPolicyInstaller()
        installer.install(source=multi_domain_policy_dir, target=target)

        assert (target / "healthcare" / "hipaa.yaml").exists()
        assert (target / "general" / "keywords.yaml").exists()

    def test_install_domain_filter(self, multi_domain_policy_dir: Path, tmp_path: Path) -> None:
        target = tmp_path / "installed"
        installer = LibraryPolicyInstaller()
        results = installer.install(
            source=multi_domain_policy_dir,
            target=target,
            domain="healthcare",
        )

        installed = [r for r in results if r.success]
        skipped = [r for r in results if r.skipped]

        assert len(installed) == 1
        assert installed[0].domain == "healthcare"
        assert len(skipped) == 1
        assert skipped[0].domain == "general"

    def test_install_dry_run_does_not_write_files(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")

        installer = LibraryPolicyInstaller()
        results = installer.install(source=source, target=target, dry_run=True)

        assert len(results) == 1
        assert results[0].dry_run is True
        assert not (target / "policy.yaml").exists()

    def test_install_no_overwrite_skips_existing(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (target / "policy.yaml").write_text("existing content", encoding="utf-8")

        installer = LibraryPolicyInstaller()
        results = installer.install(source=source, target=target, overwrite=False)

        assert results[0].skipped is True
        # Original content preserved
        assert (target / "policy.yaml").read_text() == "existing content"

    def test_install_overwrite_replaces_existing(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (target / "policy.yaml").write_text("old content", encoding="utf-8")

        installer = LibraryPolicyInstaller()
        results = installer.install(source=source, target=target, overwrite=True)

        assert results[0].success is True
        assert (target / "policy.yaml").read_text() != "old content"

    def test_install_nonexistent_source_raises(self, tmp_path: Path) -> None:
        installer = LibraryPolicyInstaller()
        with pytest.raises(ValueError, match="does not exist"):
            installer.install(source=tmp_path / "nosuchdir", target=tmp_path / "target")

    def test_install_file_as_source_raises(self, tmp_path: Path) -> None:
        source_file = tmp_path / "policy.yaml"
        source_file.write_text(_VALID_POLICY_YAML, encoding="utf-8")
        installer = LibraryPolicyInstaller()
        with pytest.raises(ValueError, match="not a directory"):
            installer.install(source=source_file, target=tmp_path / "target")

    def test_install_result_contains_policy_id(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")

        installer = LibraryPolicyInstaller()
        results = installer.install(source=source, target=target)

        assert results[0].policy_id == "test-policy-001"

    def test_list_available_returns_ids(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (source / "hipaa.yaml").write_text(_VALID_HEALTHCARE_POLICY_YAML, encoding="utf-8")

        installer = LibraryPolicyInstaller()
        ids = installer.list_available(source)

        assert "test-policy-001" in ids
        assert "test-hipaa-001" in ids

    def test_list_available_with_domain_filter(self, multi_domain_policy_dir: Path) -> None:
        installer = LibraryPolicyInstaller()
        ids = installer.list_available(multi_domain_policy_dir, domain="healthcare")
        assert "test-hipaa-001" in ids
        assert "test-policy-001" not in ids


# ===========================================================================
# CLI tests — policy list, install, validate
# ===========================================================================

class TestPolicyListCLI:
    def test_policy_list_with_source(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        (tmp_path / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, ["policy", "list", "--source", str(tmp_path)])
        assert result.exit_code == 0
        assert "test-policy-001" in result.output

    def test_policy_list_domain_filter(self, multi_domain_policy_dir: Path) -> None:
        from agent_gov.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["policy", "list", "--source", str(multi_domain_policy_dir), "--domain", "healthcare"],
        )
        assert result.exit_code == 0
        assert "test-hipaa-001" in result.output
        assert "test-policy-001" not in result.output

    def test_policy_list_severity_filter(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        (tmp_path / "medium.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")
        (tmp_path / "critical.yaml").write_text(_VALID_HEALTHCARE_POLICY_YAML, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["policy", "list", "--source", str(tmp_path), "--severity", "medium"],
        )
        assert result.exit_code == 0
        assert "test-policy-001" in result.output
        assert "test-hipaa-001" not in result.output

    def test_policy_list_invalid_source_exits_nonzero(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["policy", "list", "--source", str(tmp_path / "nonexistent")],
        )
        assert result.exit_code != 0

    def test_policy_list_empty_source_shows_no_policies(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["policy", "list", "--source", str(tmp_path)])
        assert result.exit_code == 0
        assert "No policies" in result.output


class TestPolicyInstallCLI:
    def test_policy_install_copies_files(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["policy", "install", "--source", str(source), "--target", str(target)],
        )
        assert result.exit_code == 0
        assert (target / "policy.yaml").exists()

    def test_policy_install_dry_run_does_not_write(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        (source / "policy.yaml").write_text(_VALID_POLICY_YAML, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "policy", "install",
                "--source", str(source),
                "--target", str(target),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert not (target / "policy.yaml").exists()
        assert "WOULD INSTALL" in result.output

    def test_policy_install_domain_filter(self, multi_domain_policy_dir: Path, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        target = tmp_path / "installed"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "policy", "install",
                "--source", str(multi_domain_policy_dir),
                "--target", str(target),
                "--domain", "general",
            ],
        )
        assert result.exit_code == 0
        assert (target / "general" / "keywords.yaml").exists()
        assert not (target / "healthcare" / "hipaa.yaml").exists()


class TestPolicyValidateCLI:
    def test_validate_valid_file_exits_zero(self, valid_policy_file: Path) -> None:
        from agent_gov.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["policy", "validate", str(valid_policy_file)])
        assert result.exit_code == 0
        assert "VALID" in result.output

    def test_validate_invalid_file_exits_nonzero(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        invalid_file = tmp_path / "bad.yaml"
        invalid_file.write_text(_MISSING_ID_YAML, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, ["policy", "validate", str(invalid_file)])
        assert result.exit_code != 0
        assert "INVALID" in result.output

    def test_validate_shows_error_details(self, tmp_path: Path) -> None:
        from agent_gov.cli.main import cli

        invalid_file = tmp_path / "bad.yaml"
        invalid_file.write_text(_INVALID_DOMAIN_YAML, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, ["policy", "validate", str(invalid_file)])
        assert result.exit_code != 0
        # Error message should mention what's wrong
        assert "domain" in result.output.lower() or "INVALID" in result.output


# ===========================================================================
# Library policy files — parse all 20 bundled policies
# ===========================================================================

class TestLibraryPolicyFiles:
    """Verify that every bundled policy file in policies/ is valid."""

    @pytest.fixture(autouse=True)
    def _check_library_exists(self) -> None:
        policies_dir = _policies_dir()
        if not policies_dir.exists():
            pytest.skip(f"Built-in policies directory not found: {policies_dir}")

    def _all_policy_files(self) -> list[Path]:
        return sorted(_policies_dir().rglob("*.yaml"))

    def test_at_least_20_policy_files_exist(self) -> None:
        files = self._all_policy_files()
        assert len(files) >= 20, (
            f"Expected at least 20 policy files, found {len(files)}: {files}"
        )

    @pytest.mark.parametrize(
        "expected_file",
        [
            "healthcare/hipaa_phi_protection.yaml",
            "healthcare/hipaa_minimum_necessary.yaml",
            "healthcare/hipaa_audit_trail.yaml",
            "finance/sox_data_integrity.yaml",
            "finance/pci_cardholder_data.yaml",
            "finance/financial_transaction_limits.yaml",
            "eu-ai-act/article_5_prohibited_practices.yaml",
            "eu-ai-act/article_9_risk_management.yaml",
            "eu-ai-act/article_10_data_governance.yaml",
            "eu-ai-act/article_13_transparency.yaml",
            "eu-ai-act/article_14_human_oversight.yaml",
            "eu-ai-act/article_50_ai_literacy.yaml",
            "general/pii_detection_blocking.yaml",
            "general/cost_limit_enforcement.yaml",
            "general/rate_limiting.yaml",
            "general/keyword_blocking.yaml",
            "general/output_length_limit.yaml",
            "gdpr/data_minimization.yaml",
            "gdpr/right_to_erasure.yaml",
            "gdpr/consent_management.yaml",
        ],
    )
    def test_expected_policy_file_exists(self, expected_file: str) -> None:
        full_path = _policies_dir() / expected_file
        assert full_path.exists(), f"Expected policy file not found: {full_path}"

    @pytest.mark.parametrize(
        "policy_file",
        [path.relative_to(_policies_dir()) for path in sorted(_policies_dir().rglob("*.yaml"))]
        if _policies_dir().exists()
        else [],
        ids=lambda p: str(p),
    )
    def test_every_policy_file_parses_successfully(self, policy_file: Path) -> None:
        full_path = _policies_dir() / policy_file
        loader = LibraryPolicyLoader()
        policy = loader.load_file(full_path)
        assert policy.id, f"Policy {policy_file} has empty id"
        assert policy.name, f"Policy {policy_file} has empty name"
        assert policy.domain is not None, f"Policy {policy_file} has no domain"
        assert policy.severity is not None, f"Policy {policy_file} has no severity"

    @pytest.mark.parametrize(
        "policy_file",
        [path.relative_to(_policies_dir()) for path in sorted(_policies_dir().rglob("*.yaml"))]
        if _policies_dir().exists()
        else [],
        ids=lambda p: str(p),
    )
    def test_every_policy_file_passes_validator(self, policy_file: Path) -> None:
        full_path = _policies_dir() / policy_file
        validator = LibraryPolicyValidator()
        result = validator.validate_file(full_path)
        assert result.valid is True, (
            f"Policy {policy_file} failed validation: {result.errors}"
        )

    def test_all_healthcare_policies_have_critical_or_high_severity(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            _policies_dir() / "healthcare",
            recursive=False,
            domain_filter="healthcare",
        )
        assert len(policies) == 3
        for policy in policies:
            assert policy.severity in (LibrarySeverity.CRITICAL, LibrarySeverity.HIGH), (
                f"Healthcare policy {policy.id} has unexpected severity {policy.severity}"
            )

    def test_all_eu_ai_act_policies_have_correct_domain(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            _policies_dir() / "eu-ai-act",
            recursive=False,
            domain_filter="eu-ai-act",
        )
        assert len(policies) == 6
        for policy in policies:
            assert policy.domain == LibraryDomain.EU_AI_ACT

    def test_all_gdpr_policies_have_correct_domain(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            _policies_dir() / "gdpr",
            recursive=False,
            domain_filter="gdpr",
        )
        assert len(policies) == 3
        for policy in policies:
            assert policy.domain == LibraryDomain.GDPR

    def test_all_finance_policies_have_correct_domain(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            _policies_dir() / "finance",
            recursive=False,
            domain_filter="finance",
        )
        assert len(policies) == 3
        for policy in policies:
            assert policy.domain == LibraryDomain.FINANCE

    def test_all_general_policies_have_correct_domain(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(
            _policies_dir() / "general",
            recursive=False,
            domain_filter="general",
        )
        assert len(policies) == 5
        for policy in policies:
            assert policy.domain == LibraryDomain.GENERAL

    def test_load_entire_library_recursive(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(_policies_dir(), recursive=True)
        assert len(policies) >= 20

    def test_all_policies_have_at_least_one_rule(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(_policies_dir(), recursive=True)
        for policy in policies:
            assert len(policy.rules) >= 1, (
                f"Policy {policy.id} has no rules defined"
            )

    def test_all_policies_have_unique_ids(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(_policies_dir(), recursive=True)
        ids = [p.id for p in policies]
        assert len(ids) == len(set(ids)), (
            f"Duplicate policy IDs found: {[i for i in ids if ids.count(i) > 1]}"
        )

    def test_all_policies_have_tags(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(_policies_dir(), recursive=True)
        for policy in policies:
            assert len(policy.tags) >= 1, (
                f"Policy {policy.id} has no tags"
            )

    def test_all_policies_have_references(self) -> None:
        loader = LibraryPolicyLoader()
        policies = loader.load_directory(_policies_dir(), recursive=True)
        for policy in policies:
            assert len(policy.references) >= 1, (
                f"Policy {policy.id} has no references"
            )

    def test_installer_can_install_entire_library(self, tmp_path: Path) -> None:
        target = tmp_path / "installed_policies"
        installer = LibraryPolicyInstaller()
        results = installer.install(
            source=_policies_dir(),
            target=target,
            dry_run=False,
        )
        successful = [r for r in results if r.success]
        assert len(successful) >= 20

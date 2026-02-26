"""Unit tests for agent_gov.policy.loader.

Covers PolicyLoader.load_file, load_directory, and load_string,
including error paths for missing files, invalid YAML, and schema
validation failures.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_gov.policy.loader import PolicyLoadError, PolicyLoader
from agent_gov.policy.schema import PolicyConfig

_VALID_YAML = textwrap.dedent("""\
    name: test-policy
    version: "1.0"
    description: A test policy
    rules:
      - name: block-pii
        type: pii_check
        severity: high
        params:
          check_email: true
""")

_MINIMAL_YAML = "name: minimal\n"

_INVALID_YAML = "key: [unclosed bracket"

_NON_DICT_YAML = "- item1\n- item2\n"

_SCHEMA_INVALID_YAML = textwrap.dedent("""\
    name: bad-schema
    rules:
      - type: pii_check
""")  # RuleConfig requires 'name'


class TestPolicyLoaderLoadFile:
    def test_load_valid_file(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_YAML, encoding="utf-8")
        loader = PolicyLoader()
        policy = loader.load_file(policy_file)
        assert isinstance(policy, PolicyConfig)
        assert policy.name == "test-policy"

    def test_load_yml_extension(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(_MINIMAL_YAML, encoding="utf-8")
        loader = PolicyLoader()
        policy = loader.load_file(policy_file)
        assert policy.name == "minimal"

    def test_loads_rules_correctly(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_VALID_YAML, encoding="utf-8")
        loader = PolicyLoader()
        policy = loader.load_file(policy_file)
        assert len(policy.rules) == 1
        assert policy.rules[0].type == "pii_check"

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_MINIMAL_YAML, encoding="utf-8")
        loader = PolicyLoader()
        policy = loader.load_file(str(policy_file))
        assert policy.name == "minimal"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_file(tmp_path / "nonexistent.yaml")
        assert "does not exist" in str(exc_info.value)

    def test_path_is_directory_raises(self, tmp_path: Path) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_file(tmp_path)
        assert "not a file" in str(exc_info.value)

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "bad.yaml"
        policy_file.write_text(_INVALID_YAML, encoding="utf-8")
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_file(policy_file)
        assert "YAML parse error" in str(exc_info.value)

    def test_non_dict_yaml_raises(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "list.yaml"
        policy_file.write_text(_NON_DICT_YAML, encoding="utf-8")
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_file(policy_file)
        assert "mapping" in str(exc_info.value).lower()

    def test_schema_validation_failure_raises(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "bad_schema.yaml"
        policy_file.write_text(_SCHEMA_INVALID_YAML, encoding="utf-8")
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_file(policy_file)
        assert "schema validation failed" in str(exc_info.value)

    def test_policy_load_error_has_path_attribute(self, tmp_path: Path) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_file(tmp_path / "ghost.yaml")
        assert exc_info.value.path is not None


class TestPolicyLoaderLoadDirectory:
    def test_load_single_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "policy.yaml").write_text(_MINIMAL_YAML, encoding="utf-8")
        loader = PolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 1
        assert policies[0].name == "minimal"

    def test_load_multiple_yaml_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.yaml").write_text("name: alpha\n", encoding="utf-8")
        (tmp_path / "b.yaml").write_text("name: beta\n", encoding="utf-8")
        loader = PolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 2
        names = {p.name for p in policies}
        assert names == {"alpha", "beta"}

    def test_ignores_non_yaml_files(self, tmp_path: Path) -> None:
        (tmp_path / "policy.yaml").write_text(_MINIMAL_YAML, encoding="utf-8")
        (tmp_path / "readme.txt").write_text("ignore me", encoding="utf-8")
        loader = PolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 1

    def test_skips_invalid_files_with_warning(self, tmp_path: Path) -> None:
        (tmp_path / "valid.yaml").write_text(_MINIMAL_YAML, encoding="utf-8")
        (tmp_path / "invalid.yaml").write_text(_INVALID_YAML, encoding="utf-8")
        loader = PolicyLoader()
        # Should not raise; invalid file is silently skipped
        policies = loader.load_directory(tmp_path)
        assert len(policies) == 1
        assert policies[0].name == "minimal"

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        loader = PolicyLoader()
        policies = loader.load_directory(tmp_path)
        assert policies == []

    def test_missing_directory_raises(self, tmp_path: Path) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError):
            loader.load_directory(tmp_path / "no-such-dir")

    def test_file_path_as_directory_raises(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_MINIMAL_YAML, encoding="utf-8")
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError):
            loader.load_directory(policy_file)

    def test_recursive_loads_subdirectory(self, tmp_path: Path) -> None:
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.yaml").write_text("name: nested\n", encoding="utf-8")
        loader = PolicyLoader()
        policies = loader.load_directory(tmp_path, recursive=True)
        assert any(p.name == "nested" for p in policies)

    def test_non_recursive_misses_subdirectory(self, tmp_path: Path) -> None:
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.yaml").write_text("name: nested\n", encoding="utf-8")
        loader = PolicyLoader()
        policies = loader.load_directory(tmp_path, recursive=False)
        assert not any(p.name == "nested" for p in policies)


class TestPolicyLoaderLoadString:
    def test_load_valid_string(self) -> None:
        loader = PolicyLoader()
        policy = loader.load_string(_VALID_YAML)
        assert policy.name == "test-policy"
        assert len(policy.rules) == 1

    def test_load_minimal_string(self) -> None:
        loader = PolicyLoader()
        policy = loader.load_string(_MINIMAL_YAML)
        assert policy.name == "minimal"

    def test_invalid_yaml_string_raises(self) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_string(_INVALID_YAML)
        assert "YAML parse error" in str(exc_info.value)

    def test_non_dict_yaml_string_raises(self) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError):
            loader.load_string(_NON_DICT_YAML)

    def test_schema_invalid_string_raises(self) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError):
            loader.load_string(_SCHEMA_INVALID_YAML)

    def test_custom_source_name_appears_in_error(self) -> None:
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_string(_INVALID_YAML, source_name="my-config")
        assert "my-config" in str(exc_info.value)

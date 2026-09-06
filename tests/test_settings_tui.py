"""Unit tests for the schema-driven Settings panel."""

import ki_core
import pytest
import yaml

from kicli_code_assist.ui.settings_panel import (
    SettingField,
    SettingsPanel,
    _coerce,
    _sanitize_widget_id,
    _set_by_path,
    collect_settings_fields,
    load_merged_schema,
)


@pytest.fixture
def merged_schema():
    return load_merged_schema()


@pytest.fixture
def fields(merged_schema):
    return collect_settings_fields(merged_schema)


class TestSchemaCollection:
    def test_collects_whitelisted_sections(self, fields):
        paths = {f.path for f in fields}
        assert "llm.default_provider" in paths
        assert "http.verify_ssl" in paths
        assert "security.allowed_base_path" in paths
        assert "storage.cache_dir" in paths
        assert "apps.kicli.context.max_files" in paths

    def test_excludes_sensitive_leaves(self, fields):
        paths = {f.path for f in fields}
        assert not any(p.endswith("api_key") for p in paths)

    def test_excludes_non_whitelisted_sections(self, fields):
        paths = {f.path for f in fields}
        assert not any(p.startswith("prompts.") for p in paths)
        assert not any(p.startswith("creds.") for p in paths)

    def test_enum_field_detected(self, fields):
        diff_format = next(f for f in fields if f.path == "apps.kicli.diff.format")
        assert diff_format.enum == ["unified", "context", "side-by-side"]

    def test_field_types(self, fields):
        by_path = {f.path: f for f in fields}
        assert by_path["http.request_timeout"].field_type == "integer"
        assert by_path["http.verify_ssl"].field_type == "boolean"
        assert by_path["security.allowed_base_path"].field_type == "string"


class TestWidgetId:
    def test_sanitize_widget_id_is_stable_and_valid(self):
        wid = _sanitize_widget_id("apps.kicli.diff.max_file_size_kb")
        assert wid == "field_apps_kicli_diff_max_file_size_kb"
        assert wid == _sanitize_widget_id("apps.kicli.diff.max_file_size_kb")


class TestSetByPath:
    def test_sets_nested_value_creating_dicts(self):
        data = {}
        _set_by_path(data, "apps.kicli.diff.format", "context")
        assert data == {"apps": {"kicli": {"diff": {"format": "context"}}}}

    def test_preserves_sibling_keys(self):
        data = {"apps": {"kicli": {"diff": {"context_lines": 3}}}}
        _set_by_path(data, "apps.kicli.diff.format", "context")
        assert data["apps"]["kicli"]["diff"] == {
            "context_lines": 3,
            "format": "context",
        }


class TestCoerce:
    def test_coerce_integer(self):
        assert _coerce("42", "integer") == 42

    def test_coerce_number(self):
        assert _coerce("0.5", "number") == 0.5

    def test_coerce_string_passthrough(self):
        assert _coerce("hello", "string") == "hello"


class TestSettingsPanelSave:
    def test_save_merges_onto_existing_file(self, tmp_path):
        config_path = tmp_path / "ki.yaml"
        config_path.write_text(yaml.safe_dump({"prompts": {"active_role": "coder"}}))

        panel = SettingsPanel.__new__(SettingsPanel)
        panel.raw_config = {}
        panel.config_path = config_path
        panel.fields = [
            SettingField(
                path="http.request_timeout",
                section="HTTP Client Settings",
                field_type="integer",
                title="Request Timeout",
            )
        ]

        # Bypass widget querying by monkeypatching collect_values directly.
        panel.collect_values = lambda: {"http.request_timeout": 45}
        saved_path = panel.save()

        assert saved_path == config_path
        on_disk = yaml.safe_load(config_path.read_text())
        assert on_disk["prompts"] == {"active_role": "coder"}
        assert on_disk["http"]["request_timeout"] == 45

    def test_save_creates_file_when_missing(self, tmp_path):
        config_path = tmp_path / "nested" / "ki.yaml"

        panel = SettingsPanel.__new__(SettingsPanel)
        panel.raw_config = {}
        panel.config_path = config_path
        panel.fields = []
        panel.collect_values = lambda: {"storage.cache_dir": "/tmp/cache"}

        panel.save()
        assert config_path.exists()
        on_disk = yaml.safe_load(config_path.read_text())
        assert on_disk["storage"]["cache_dir"] == "/tmp/cache"


def test_find_config_path_default_is_ki_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ki_core.find_config_path() == pytest.importorskip("pathlib").Path("ki.yaml")

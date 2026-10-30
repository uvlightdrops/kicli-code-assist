"""Unit tests for the schema-driven Settings panel."""

import ki_core
import pytest
import yaml
from pathlib import Path

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
        assert "llm.provider" in paths
        assert "agent.intervention.mode" in paths
        assert "web.port" in paths
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


REPO_ROOT = Path(__file__).resolve().parents[1]


def _project(tmp_path, monkeypatch, ki_yaml: dict):
    import shutil
    shutil.copytree(REPO_ROOT / "schema", tmp_path / "schema")
    (tmp_path / "ki.yaml").write_text(yaml.safe_dump(ki_yaml))
    monkeypatch.chdir(tmp_path)
    for key in [k for k in __import__("os").environ if k.startswith("KI_CFG_")]:
        monkeypatch.delenv(key)
    monkeypatch.delenv("KI_STAGE", raising=False)
    monkeypatch.delenv("KI_PROFILE", raising=False)
    return tmp_path / "ki.yaml"


class TestSettingsPanelSave:
    def test_save_writes_runtime_override_not_ki_yaml(self, tmp_path, monkeypatch):
        config_path = _project(tmp_path, monkeypatch, {"llm": {"provider": "mock"}})
        before = config_path.read_text()

        panel = SettingsPanel.__new__(SettingsPanel)
        panel.raw_config = {}
        panel.config_path = config_path
        panel.fields = []
        panel.collect_values = lambda: {"http.request_timeout": 45}
        saved_path = panel.save()

        assert saved_path == tmp_path / "config" / "runtime" / "runtime.yaml"
        assert config_path.read_text() == before
        on_disk = yaml.safe_load(saved_path.read_text())
        assert on_disk == {"http": {"request_timeout": 45}}

    def test_save_only_writes_changed_values(self, tmp_path, monkeypatch):
        config_path = _project(tmp_path, monkeypatch, {"http": {"request_timeout": 30}})

        panel = SettingsPanel.__new__(SettingsPanel)
        panel.raw_config = {}
        panel.config_path = config_path
        panel.fields = []
        panel.collect_values = lambda: {
            "http.request_timeout": 30,
            "storage.cache_dir": "cache-dir",
            "llm.providers.openai.api_key": "not-written",
        }
        target = panel.save()
        on_disk = yaml.safe_load(target.read_text())
        assert on_disk == {"storage": {"cache_dir": "cache-dir"}}


def test_find_config_path_default_is_ki_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ki_core.find_config_path() == pytest.importorskip("pathlib").Path("ki.yaml")

"""Settings panel for TUI - schema-driven editor for yaml-cfg-wizard config.

Rather than hardcoding a field list, this walks the merged JSON schema
(ki-core's generic base schema + this app's schema/kicli.schema.yaml) to
discover editable fields, their types, defaults, and validation rules.
Current values come from the already-resolved config (AppConfig.raw).
Saving writes only the edited dotted-paths back onto whatever the active
ki.yaml file already contains, leaving untouched sections (creds, prompts,
custom provider keys, ...) exactly as they were.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.widgets import Static, Button, Label, Input, Switch, Select
from textual.binding import Binding
from textual.message import Message
from textual.screen import ModalScreen
from textual.validation import Integer, Number

import ki_core
from yaml_cfg_wizard.schema_utils import merge_schemas

# Top-level schema sections exposed in the settings UI. "creds" (secrets)
# and "prompts" (already has its own dedicated Ctrl+O modal) are
# intentionally excluded.
WHITELISTED_SECTIONS = ["llm", "http", "security", "storage", "apps.kicli"]

# Leaf field names that hold secrets and must never show up in a plain
# editable text field, even if their parent section is whitelisted.
SENSITIVE_LEAF_NAMES = {"api_key", "password", "secret", "token"}


def _sanitize_widget_id(dotted_path: str) -> str:
    """Turn a dotted config path into a valid Textual widget id."""
    return "field_" + re.sub(r"[^a-zA-Z0-9_-]", "_", dotted_path)


@dataclass
class SettingField:
    """Metadata + widget id for one editable config field."""

    path: str
    section: str
    field_type: str
    title: str
    description: str = ""
    default: Any = None
    enum: Optional[list] = field(default=None)
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    @property
    def widget_id(self) -> str:
        return _sanitize_widget_id(self.path)

    @property
    def label(self) -> str:
        return self.title or self.path.rsplit(".", 1)[-1].replace("_", " ").title()


def load_merged_schema(start: Optional[Path] = None) -> dict:
    """Load the merged ki-core + app schema as a plain dict."""
    schema_paths = ki_core.get_merged_schemas(start)
    return merge_schemas(*schema_paths)


def _collect_fields(node: dict, path_prefix: str, section: str, out: list) -> None:
    """Recursively walk schema `properties`, collecting leaf fields."""
    for key, subschema in (node.get("properties") or {}).items():
        if key in SENSITIVE_LEAF_NAMES:
            continue
        new_path = f"{path_prefix}.{key}" if path_prefix else key
        node_type = subschema.get("type")
        if node_type == "object" and "properties" in subschema:
            _collect_fields(subschema, new_path, subschema.get("title", section), out)
        elif node_type in ("string", "integer", "number", "boolean"):
            out.append(
                SettingField(
                    path=new_path,
                    section=section,
                    field_type=node_type,
                    title=subschema.get("title", ""),
                    description=subschema.get("description", ""),
                    default=subschema.get("default"),
                    enum=subschema.get("enum"),
                    minimum=subschema.get("minimum"),
                    maximum=subschema.get("maximum"),
                )
            )


def collect_settings_fields(schema: dict) -> list:
    """Flatten the whitelisted sections of `schema` into SettingFields."""
    fields: list = []
    properties = schema.get("properties") or {}
    for section_path in WHITELISTED_SECTIONS:
        node = {"properties": properties}
        found = True
        for part in section_path.split("."):
            props = node.get("properties") or {}
            if part not in props:
                found = False
                break
            node = props[part]
        if not found:
            continue
        section_title = node.get("title", section_path)
        _collect_fields(node, section_path, section_title, fields)
    return fields


def _set_by_path(data: dict, dotted_path: str, value: Any) -> None:
    """Set `value` at `dotted_path` in `data`, creating nested dicts as needed."""
    parts = dotted_path.split(".")
    current = data
    for part in parts[:-1]:
        nxt = current.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            current[part] = nxt
        current = nxt
    current[parts[-1]] = value


def _coerce(value: str, field_type: str) -> Any:
    if field_type == "integer":
        return int(value)
    if field_type == "number":
        return float(value)
    return value


class SettingsSaved(Message):
    """Posted when settings have been written back to the config file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class SettingsPanel(Vertical):
    """Schema-driven settings form."""

    can_focus = True

    DEFAULT_CSS = """
    SettingsPanel {
        height: auto;
        max-height: 100%;
    }
    SettingsPanel .section-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
    }
    SettingsPanel .field-row {
        height: auto;
        margin-bottom: 1;
    }
    SettingsPanel .field-label {
        width: 40;
        content-align: left middle;
    }
    SettingsPanel .field-input {
        width: 1fr;
    }
    SettingsPanel #settings-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(self, raw_config: dict, config_path: Optional[Path] = None):
        super().__init__()
        self.raw_config = raw_config
        self.config_path = config_path or ki_core.find_config_path()
        self.fields: list = collect_settings_fields(load_merged_schema())
        self.status_label: Optional[Static] = None

    def compose(self):
        with VerticalScroll(id="settings-scroll"):
            current_section = None
            for f in self.fields:
                if f.section != current_section:
                    current_section = f.section
                    yield Static(current_section, classes="section-title")
                yield from self._compose_field(f)
            yield Static("", id="settings-status")
        with Horizontal(id="settings-buttons"):
            yield Button("Save", id="save-settings", variant="success")
            yield Button("Cancel", id="cancel-settings", variant="default")

    def _compose_field(self, f: SettingField):
        current = self.raw_config.get_path(f.path, f.default) if hasattr(
            self.raw_config, "get_path"
        ) else f.default
        label_text = f.label
        if f.description:
            label_text = f"{f.label}\n[dim]{f.description}[/dim]"
        with Horizontal(classes="field-row"):
            yield Label(label_text, classes="field-label")
            if f.enum:
                options = [(str(opt), str(opt)) for opt in f.enum]
                yield Select(
                    options,
                    value=str(current) if current is not None else None,
                    id=f.widget_id,
                    classes="field-input",
                )
            elif f.field_type == "boolean":
                yield Switch(value=bool(current), id=f.widget_id, classes="field-input")
            else:
                validators = []
                if f.field_type == "integer":
                    validators.append(Integer(minimum=f.minimum, maximum=f.maximum))
                elif f.field_type == "number":
                    validators.append(Number(minimum=f.minimum, maximum=f.maximum))
                yield Input(
                    value="" if current is None else str(current),
                    id=f.widget_id,
                    classes="field-input",
                    validators=validators or None,
                )

    def collect_values(self) -> dict:
        """Read current widget values and return a dotted-path -> value dict."""
        values = {}
        for f in self.fields:
            widget = self.query_one(f"#{f.widget_id}")
            if isinstance(widget, Switch):
                values[f.path] = widget.value
            elif isinstance(widget, Select):
                if widget.value is not None:
                    values[f.path] = widget.value
            elif isinstance(widget, Input):
                if widget.value != "":
                    values[f.path] = _coerce(widget.value, f.field_type)
        return values

    def save(self) -> Path:
        """Merge edited values onto the on-disk YAML file and write it back."""
        values = self.collect_values()
        on_disk: dict = {}
        if self.config_path.exists():
            on_disk = yaml.safe_load(self.config_path.read_text()) or {}
        for dotted_path, value in values.items():
            _set_by_path(on_disk, dotted_path, value)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(yaml.safe_dump(on_disk, sort_keys=False))
        return self.config_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-settings":
            path = self.save()
            self.post_message(SettingsSaved(path))
        elif event.button.id == "cancel-settings":
            self.app.pop_screen()


class SettingsModal(ModalScreen):
    """Modal dialog for editing yaml-cfg-wizard settings."""

    CSS = """
    SettingsModal {
        align: center middle;
        background: $surface 50%;
    }

    SettingsModal SettingsPanel {
        width: 110;
        height: 42;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close_modal", "Close", show=True),
    ]

    def __init__(self, raw_config: dict, config_path: Optional[Path] = None):
        super().__init__()
        self.raw_config = raw_config
        self.config_path = config_path
        self.settings_panel: Optional[SettingsPanel] = None

    def compose(self):
        self.settings_panel = SettingsPanel(self.raw_config, self.config_path)
        yield self.settings_panel

    def on_mount(self) -> None:
        self.call_after_refresh(self._ensure_focus)

    def _ensure_focus(self) -> None:
        if self.settings_panel:
            self.settings_panel.focus()

    def on_settings_saved(self, message: SettingsSaved) -> None:
        if self.settings_panel:
            status = self.settings_panel.query_one("#settings-status", Static)
            status.update(f"[green]Saved to {message.path}[/green]")

    def action_close_modal(self) -> None:
        self.app.pop_screen()

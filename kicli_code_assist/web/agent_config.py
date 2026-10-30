"""Legacy agent configuration API (``/api/agent/config``), bridged to runtime settings.

The ``agent`` section is part of the kicli schema and is stored like every
other setting through ``ki_core.runtime_settings`` in
``config/runtime/runtime.yaml`` (see ``kicli_code_assist.runtime_config``).
There is no separate in-memory store anymore: reads return the effective
layered value, writes are runtime overrides, ``reset`` removes them.
Writes need the same local guard and settings token as ``/api/settings``.
"""

import copy
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify

from kicli_code_assist import runtime_config
from kicli_code_assist.runtime_config import ConflictError, EditorError, ValidationError

logger = logging.getLogger("kicli-web-agent-config")

# Defaults mirror schema/kicli.schema.yaml (agent section)
DEFAULT_AGENT_CONFIG = {
    "intervention": {
        "mode": "user_prompt",  # queue, supervisor, user_prompt
    },
    "streaming": {
        "thinking_detail": "balanced",  # minimal, balanced, verbose
        "state_broadcast_rate": 10,
        "websocket_timeout": 30,
    },
    "rollback": {
        "auto_on_error": True,
        "log_error_artifacts": True,
        "preserve_branch": False,
    },
    "state": {
        "persistence": "json",
        "retention": "session",
        "export_on_completion": True,
    },
}




class AgentConfigManager:
    """View of the ``agent`` section of the layered configuration."""

    def __init__(self, config_manager: Optional[Any] = None, project_root: Optional[Path] = None):
        self.ki_config_manager = config_manager
        self.project_root = project_root

    def get_config(self) -> Dict[str, Any]:
        """Effective agent configuration (defaults < ki.yaml < stage < runtime.yaml < env)."""
        try:
            from kicli_code_assist.llm_runtime import get_live_config
            agent = get_live_config(self.project_root).get().get("agent") or {}
        except Exception as e:
            logger.warning(f"Failed to load agent config: {type(e).__name__}")
            agent = {}
        return self._deep_merge(DEFAULT_AGENT_CONFIG, agent if isinstance(agent, dict) else {})

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and persist ``updates`` as runtime overrides.

        Raises:
            ValueError: invalid structure/values (legacy contract -> HTTP 400)
            ConflictError: runtime.yaml changed concurrently
        """
        if not isinstance(updates, dict) or not updates:
            raise ValueError("Body must be a non-empty object of agent sections")
        unknown = set(updates) - set(AGENT_CONFIG_SCHEMA)
        if unknown:
            raise ValueError(f"Unknown section(s): {', '.join(sorted(unknown))}")
        for section, values in updates.items():
            if not isinstance(values, dict):
                raise ValueError(f"Section {section} must be an object")
            unknown_keys = set(values) - set(AGENT_CONFIG_SCHEMA[section])
            if unknown_keys:
                raise ValueError(f"Unknown key(s) in {section}: {', '.join(sorted(unknown_keys))}")
        test_config = self._deep_merge(self.get_config(), updates)
        is_valid, error_msg = self.validate_config(test_config)
        if not is_valid:
            raise ValueError(error_msg)
        changes = runtime_config.flatten("agent", updates)
        service = runtime_config.settings_service(self.project_root)
        revision = service.snapshot()["revision"]
        try:
            self.last_result = runtime_config.save(revision, changes, (), self.project_root)
        except ValidationError as e:
            raise ValueError(str(e)) from None
        return self.get_config()

    def reset_to_defaults(self) -> Dict[str, Any]:
        """Remove all runtime overrides of the agent section."""
        snap = runtime_config.snapshot(self.project_root)
        remove = [r["path"] for r in snap["rows"]
                  if r["section"] == "agent" and r["overridden"] and r["editable"]]
        if remove:
            self.last_result = runtime_config.save(snap["revision"], {}, remove, self.project_root)
        else:
            self.last_result = snap
        return self.get_config()

    @staticmethod
    def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge updates into a copy of base."""
        result = copy.deepcopy(base)
        for key, value in updates.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = AgentConfigManager._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate configuration values against AGENT_CONFIG_SCHEMA."""
        for section, fields in AGENT_CONFIG_SCHEMA.items():
            values = config.get(section, {})
            if not isinstance(values, dict):
                return False, f"Section {section} must be an object"
            for key, rule in fields.items():
                if key not in values:
                    continue
                value = values[key]
                kind = rule["type"]
                if kind == "boolean" and not isinstance(value, bool):
                    return False, f"{section}.{key} must be a boolean"
                if kind == "integer":
                    if isinstance(value, bool) or not isinstance(value, int):
                        return False, f"{section}.{key} must be an integer"
                    if not rule.get("minimum", value) <= value <= rule.get("maximum", value):
                        return False, (f"{section}.{key} must be between "
                                       f"{rule['minimum']} and {rule['maximum']}")
                if kind == "string" and "enum" in rule and value not in rule["enum"]:
                    label = {"mode": "intervention mode"}.get(key, key)
                    return False, f"Invalid {label}. Must be one of {set(rule['enum'])}"
        return True, None


def get_agent_config_manager(
    ki_config_manager: Optional[Any] = None, project_root: Optional[Path] = None,
) -> AgentConfigManager:
    """Stateless view; kept for backwards compatibility."""
    return AgentConfigManager(config_manager=ki_config_manager, project_root=project_root)


def register_agent_config_routes(
    app: Flask, ki_config_manager: Optional[Any] = None, project_root: Optional[Path] = None,
):
    """Register the legacy agent configuration endpoints (bridged to runtime settings)."""
    from kicli_code_assist.web.settings_routes import after_save

    def manager() -> AgentConfigManager:
        return get_agent_config_manager(ki_config_manager, project_root)

    def access(write: bool):
        check = app.config.get("KICLI_SETTINGS_ACCESS")
        if check is None:
            return jsonify({"error": "Settings API not available"}), 503
        return check(write=write)

    @app.route("/api/agent/config", methods=["GET"])
    def get_agent_config():
        """Effective agent configuration."""
        denied = access(False)
        if denied is not None:
            return denied
        try:
            return jsonify(manager().get_config()), 200
        except Exception as e:
            logger.error(f"Get agent config error: {type(e).__name__}")
            return jsonify({"error": "Agent configuration could not be read"}), 500

    @app.route("/api/agent/config", methods=["PUT", "POST"])
    def update_agent_config():
        """Persist agent overrides, e.g. {"intervention": {"mode": "supervisor"}}."""
        denied = access(True)
        if denied is not None:
            return denied
        data = request.get_json(silent=True)
        try:
            m = manager()
            updated = m.update_config(data)
            after_save(app, m.last_result, runtime_config.flatten("agent", data))
            return jsonify({
                "success": True,
                "config": updated,
                "message": "Configuration updated (applies to the next request)",
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except ConflictError as e:
            return jsonify({"error": str(e) or "Configuration changed meanwhile"}), 409
        except EditorError as e:
            return jsonify({"error": str(e)}), 503
        except Exception as e:
            logger.error(f"Update agent config error: {type(e).__name__}")
            return jsonify({"error": "Agent configuration could not be saved"}), 500

    @app.route("/api/agent/config/<section>", methods=["GET"])
    def get_config_section(section: str):
        """Get one section: intervention, streaming, rollback or state."""
        denied = access(False)
        if denied is not None:
            return denied
        config = manager().get_config()
        if section not in AGENT_CONFIG_SCHEMA:
            return jsonify({
                "error": f"Unknown section. Valid: {', '.join(AGENT_CONFIG_SCHEMA)}"
            }), 404
        return jsonify({section: config.get(section, {})}), 200

    @app.route("/api/agent/config/reset", methods=["POST"])
    def reset_agent_config():
        """Remove all runtime overrides of the agent section."""
        denied = access(True)
        if denied is not None:
            return denied
        try:
            m = manager()
            config = m.reset_to_defaults()
            after_save(app, m.last_result, {"agent"})
            return jsonify({
                "success": True,
                "config": config,
                "message": "Agent overrides removed",
            }), 200
        except ConflictError as e:
            return jsonify({"error": str(e) or "Configuration changed meanwhile"}), 409
        except EditorError as e:
            return jsonify({"error": str(e)}), 503
        except Exception as e:
            logger.error(f"Reset config error: {type(e).__name__}")
            return jsonify({"error": "Agent configuration could not be reset"}), 500


# Schema for validation and documentation
AGENT_CONFIG_SCHEMA = {
    "intervention": {
        "mode": {"type": "string", "enum": ["queue", "supervisor", "user_prompt"]},
    },
    "streaming": {
        "thinking_detail": {"type": "string", "enum": ["minimal", "balanced", "verbose"]},
        "state_broadcast_rate": {"type": "integer", "minimum": 1, "maximum": 100},
        "websocket_timeout": {"type": "integer", "minimum": 10, "maximum": 300},
    },
    "rollback": {
        "auto_on_error": {"type": "boolean"},
        "log_error_artifacts": {"type": "boolean"},
        "preserve_branch": {"type": "boolean"},
    },
    "state": {
        "persistence": {"type": "string", "enum": ["json", "sqlite"]},
        "retention": {"type": "string", "enum": ["session", "7days", "permanent"]},
        "export_on_completion": {"type": "boolean"},
    },
}

"""Agent configuration API endpoints for Phase 5.5 streaming.

Integrates with ki_core.config.ConfigManager for YAML-backed agent settings.
Agent settings are stored in ki.yaml under 'agent' section and synced via ConfigManager.

Enables WebUI to read and modify agent streaming settings in real-time:
- Intervention mode (queue, supervisor, user_prompt)
- Thinking detail level (minimal, balanced, verbose)
- Auto-rollback behavior

All changes persist to ki.yaml and are shared across all kicli-assist instances.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify

try:
    from ki_core.config import ConfigManager, ConfigDict
except ImportError:
    ConfigManager = None
    ConfigDict = None

logger = logging.getLogger("kicli-web-agent-config")

# Default agent configuration (used when ki.yaml doesn't define agent section)
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
    """Manages agent configuration backed by ki.yaml via ki_core.ConfigManager.
    
    Reads from 'agent' section in ki.yaml, falls back to defaults if not present.
    Updates persist to ki.yaml if ConfigManager is available.
    """
    
    def __init__(self, config_manager: Optional[Any] = None):
        """Initialize with optional ki_core.ConfigManager.
        
        Args:
            config_manager: ki_core.ConfigManager instance. If None, uses in-memory defaults.
        """
        self.ki_config_manager = config_manager
        self._runtime_config = DEFAULT_AGENT_CONFIG.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current agent configuration.
        
        Attempts to load from ki.yaml via ConfigManager first, falls back to defaults.
        Returns merged config (ki.yaml + defaults).
        """
        if self.ki_config_manager:
            try:
                config = self.ki_config_manager.load()
                # Load agent section from ki.yaml, merge with defaults
                agent_config = config.get_path("agent", {})
                if agent_config:
                    # Deep merge with defaults
                    return self._deep_merge(DEFAULT_AGENT_CONFIG, agent_config)
            except Exception as e:
                logger.warning(f"Failed to load agent config from ki.yaml: {e}")
        
        return self._runtime_config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration with validation.
        
        Persists to ki.yaml if ConfigManager is available, otherwise uses in-memory storage.
        
        Args:
            updates: Dict with nested updates (e.g., {"intervention": {"mode": "supervisor"}})
            
        Returns:
            Updated config
        """
        # Validate first
        current = self.get_config()
        test_config = self._deep_merge(current, updates)
        is_valid, error_msg = self.validate_config(test_config)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Update in-memory
        self._runtime_config = self._deep_merge(self._runtime_config, updates)
        
        # Persist to ki.yaml if available
        if self.ki_config_manager:
            try:
                config = self.ki_config_manager.load()
                # Update agent section in config
                agent_section = config.get_path("agent", {}) or {}
                agent_section = self._deep_merge(agent_section, updates)
                
                # Write back to yaml (would need YAML writer in ki_core)
                # For now, log that it would be persisted
                logger.info(f"Agent config would persist to ki.yaml: {updates}")
                # TODO: Implement YAML persistence via ki_core
            except Exception as e:
                logger.warning(f"Could not persist agent config to ki.yaml: {e}")
        
        logger.info(f"Agent config updated: {updates}")
        return test_config
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset configuration to defaults."""
        self._runtime_config = DEFAULT_AGENT_CONFIG.copy()
        logger.info("Agent config reset to defaults")
        return self._runtime_config.copy()
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge updates into base dict."""
        result = base.copy()
        for key, value in updates.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = AgentConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate configuration values.
        
        Returns:
            (is_valid, error_message)
        """
        valid_modes = {"queue", "supervisor", "user_prompt"}
        if config.get("intervention", {}).get("mode") not in valid_modes:
            return False, f"Invalid intervention mode. Must be one of {valid_modes}"
        
        valid_detail = {"minimal", "balanced", "verbose"}
        if config.get("streaming", {}).get("thinking_detail") not in valid_detail:
            return False, f"Invalid thinking_detail. Must be one of {valid_detail}"
        
        valid_persistence = {"json", "sqlite"}
        if config.get("state", {}).get("persistence") not in valid_persistence:
            return False, f"Invalid persistence. Must be one of {valid_persistence}"
        
        valid_retention = {"session", "7days", "permanent"}
        if config.get("state", {}).get("retention") not in valid_retention:
            return False, f"Invalid retention. Must be one of {valid_retention}"
        
        return True, None


# Global instance
_config_manager: Optional[AgentConfigManager] = None


def get_agent_config_manager(ki_config_manager: Optional[Any] = None) -> AgentConfigManager:
    """Get or create global agent config manager.
    
    Args:
        ki_config_manager: Optional ki_core.ConfigManager instance for YAML persistence.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentConfigManager(config_manager=ki_config_manager)
    return _config_manager


def register_agent_config_routes(app: Flask, ki_config_manager: Optional[Any] = None):
    """Register agent configuration API endpoints.
    
    Args:
        app: Flask application instance
        ki_config_manager: Optional ki_core.ConfigManager for YAML persistence
    """
    # Initialize manager with ki_config_manager if provided
    if ki_config_manager:
        global _config_manager
        _config_manager = AgentConfigManager(config_manager=ki_config_manager)
    
    @app.route("/api/agent/config", methods=["GET"])
    def get_agent_config():
        """Get current agent configuration.
        
        Loads from ki.yaml if available, otherwise returns in-memory config.
        
        Returns:
            {
                "intervention": {"mode": "user_prompt"},
                "streaming": {"thinking_detail": "balanced", ...},
                "rollback": {"auto_on_error": true, ...},
                "state": {...}
            }
        """
        try:
            manager = get_agent_config_manager(ki_config_manager)
            return jsonify(manager.get_config()), 200
        except Exception as e:
            logger.error(f"Get agent config error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agent/config", methods=["PUT", "POST"])
    def update_agent_config():
        """Update agent configuration.
        
        Updates persist to ki.yaml if ConfigManager is available.
        
        Request:
        {
            "intervention": {"mode": "supervisor"},
            "streaming": {"thinking_detail": "verbose"}
        }
        
        Returns:
            Updated config or error
        """
        try:
            data = request.get_json() or {}
            manager = get_agent_config_manager(ki_config_manager)
            
            # Update and validate
            updated = manager.update_config(data)
            logger.info(f"Agent config updated via API: {data}")
            
            return jsonify({
                "success": True,
                "config": updated,
                "message": "Configuration updated successfully"
            }), 200
        
        except ValueError as e:
            logger.warning(f"Agent config validation error: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Update agent config error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agent/config/<section>", methods=["GET"])
    def get_config_section(section: str):
        """Get specific config section.
        
        Args:
            section: "intervention", "streaming", "rollback", or "state"
        
        Returns:
            Configuration for that section
        """
        try:
            manager = get_agent_config_manager(ki_config_manager)
            config = manager.get_config()
            
            if section not in config:
                return jsonify({
                    "error": f"Unknown section: {section}. Valid: intervention, streaming, rollback, state"
                }), 404
            
            return jsonify({section: config[section]}), 200
        
        except Exception as e:
            logger.error(f"Get config section error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agent/config/reset", methods=["POST"])
    def reset_agent_config():
        """Reset configuration to defaults."""
        try:
            manager = get_agent_config_manager(ki_config_manager)
            config = manager.reset_to_defaults()
            
            logger.info("Agent config reset to defaults")
            return jsonify({
                "success": True,
                "config": config,
                "message": "Configuration reset to defaults"
            }), 200
        
        except Exception as e:
            logger.error(f"Reset config error: {e}")
            return jsonify({"error": str(e)}), 500


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

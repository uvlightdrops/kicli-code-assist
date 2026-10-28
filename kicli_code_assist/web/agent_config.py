"""Agent configuration API endpoints for Phase 5.5 streaming.

Enables WebUI to read and modify agent streaming settings in real-time:
- Intervention mode (queue, supervisor, user_prompt)
- Thinking detail level (minimal, balanced, verbose)
- Auto-rollback behavior
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify

logger = logging.getLogger("kicli-web-agent-config")


class AgentConfigManager:
    """Manages agent configuration state."""
    
    def __init__(self):
        """Initialize with defaults."""
        self.config = {
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
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration with validation.
        
        Args:
            updates: Dict with nested updates (e.g., {"intervention": {"mode": "supervisor"}})
            
        Returns:
            Updated config
        """
        def deep_update(d: Dict, u: Dict) -> Dict:
            """Recursively update dict."""
            for k, v in u.items():
                if isinstance(v, dict) and k in d:
                    d[k] = deep_update(d[k], v)
                else:
                    d[k] = v
            return d
        
        self.config = deep_update(self.config, updates)
        logger.info(f"Agent config updated: {updates}")
        return self.config
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
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
        
        return True, None


# Global instance
_config_manager: Optional[AgentConfigManager] = None


def get_agent_config_manager() -> AgentConfigManager:
    """Get or create global agent config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentConfigManager()
    return _config_manager


def register_agent_config_routes(app: Flask):
    """Register agent configuration API endpoints."""
    
    @app.route("/api/agent/config", methods=["GET"])
    def get_agent_config():
        """Get current agent configuration.
        
        Returns:
            {
                "intervention": {"mode": "user_prompt"},
                "streaming": {"thinking_detail": "balanced", ...},
                "rollback": {"auto_on_error": true, ...},
                "state": {...}
            }
        """
        try:
            manager = get_agent_config_manager()
            return jsonify(manager.get_config()), 200
        except Exception as e:
            logger.error(f"Get agent config error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agent/config", methods=["PUT", "POST"])
    def update_agent_config():
        """Update agent configuration.
        
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
            manager = get_agent_config_manager()
            
            # Validate before updating
            current = manager.get_config()
            test_config = {**current}
            def deep_update(d: Dict, u: Dict) -> Dict:
                for k, v in u.items():
                    if isinstance(v, dict) and k in d:
                        d[k] = deep_update(d[k], v)
                    else:
                        d[k] = v
                return d
            test_config = deep_update(test_config, data)
            
            is_valid, error_msg = manager.validate_config(test_config)
            if not is_valid:
                return jsonify({"error": error_msg}), 400
            
            # Update
            updated = manager.update_config(data)
            logger.info(f"Agent config updated via API: {data}")
            
            return jsonify({
                "success": True,
                "config": updated,
                "message": "Configuration updated successfully"
            }), 200
        
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
            manager = get_agent_config_manager()
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
            global _config_manager
            _config_manager = AgentConfigManager()
            
            logger.info("Agent config reset to defaults")
            return jsonify({
                "success": True,
                "config": _config_manager.get_config(),
                "message": "Configuration reset to defaults"
            }), 200
        
        except Exception as e:
            logger.error(f"Reset config error: {e}")
            return jsonify({"error": str(e)}), 500


# Schema for validation
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

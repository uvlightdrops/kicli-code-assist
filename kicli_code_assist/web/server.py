"""
Flask backend server for web IDE.

Serves REST API + WebSocket for real-time chat streaming.
Reads config from ki.yaml and logs to ~/dev_data/kicli-code-assist/log/

Architecture (Phases 1-4 Modularization):
- server_config.py: Configuration and logging setup
- server_instances.py: Phase 2D singleton instances
- server_routes.py: REST API endpoints (Phase 2D unified router)
- server_websocket.py: WebSocket event handlers
- server_async.py: Async LLM processing and streaming
"""

import os
import sys
import logging
import secrets
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.logging_integration import _get_log_dir

# Import refactored modules (Phase 1)
from kicli_code_assist.web.server_config import (
    get_config, setup_logging, get_cors_origins, get_web_settings
)

# Import route registration (Phase 2)
from kicli_code_assist.web.server_routes import (
    register_routes, register_project_routes, register_server_management_routes
)

# Import WebSocket registration (Phase 3)
from kicli_code_assist.web.server_websocket import register_websocket

# Import agent config routes (Phase 5.5)
from kicli_code_assist.web.agent_config import register_agent_config_routes

# Runtime settings (shared ki_core.runtime_settings service)
from kicli_code_assist.web.settings_routes import register_settings_routes
from kicli_code_assist.llm_runtime import get_live_config


def create_app(
    config: Optional[Dict] = None, project_root: Optional[Path] = None,
) -> tuple[Flask, SocketIO]:
    """Create and configure Flask app with SocketIO.
    
    Integrates all refactored modules (Phases 1-4) into a single app.
    
    Args:
        config: Optional fixed configuration dict (tests). If None, the app
            runs in live mode: ``app.config["KICLI_CONFIG"]`` is refreshed
            from the layered ki-core config before every request, so
            runtime.yaml/creds.yaml/stage edits apply without restart.
        project_root: Project whose ``config/`` tree is used (default: cwd
            or the directory of the discovered ki.yaml).
        
    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("KICLI_WEB_SECRET_KEY") or secrets.token_hex(32)
    
    live = None
    if config is None:
        try:
            live = get_live_config(project_root)
            config = live.get()
        except Exception as e:
            logging.getLogger("kicli-web").error(f"Live config unavailable: {type(e).__name__}")
            config = get_config()
    
    # Initialize ki_core ConfigManager for YAML persistence
    try:
        from ki_core.config import ConfigManager
        ki_config_manager = ConfigManager()
    except (ImportError, Exception) as e:
        ki_config_manager = None
        app.logger.debug(f"ki_core ConfigManager not available: {e}")
    
    # Store config in app context
    app.config["KICLI_CONFIG"] = config
    app.config["KICLI_LIVE_CONFIG"] = live
    app.config["KI_CONFIG_MANAGER"] = ki_config_manager
    app.config["ACTIVE_REQUESTS"] = {}
    app.config["CHAT_SESSION"] = ChatSession()

    def refresh_config(force: bool = False) -> None:
        """Pick up config changes; drop clients that cached the old LLM settings."""
        if live is None:
            return
        if force:
            live.invalidate()
        previous = app.config.get("KICLI_CONFIG")
        current = live.get()
        app.config["KICLI_CONFIG"] = current
        if current is not previous:
            from kicli_code_assist.llm_integration import reset_async_integration
            reset_async_integration()

    app.config["KICLI_REFRESH_CONFIG"] = refresh_config
    if live is not None:
        @app.before_request
        def _refresh_live_config():
            refresh_config()
    
    # Setup logging
    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logging(config)
    app.logger = logger
    
    # Setup CORS
    cors_origins = get_cors_origins(config)
    CORS(app, origins=cors_origins)
    
    # Create SocketIO instance
    socketio = SocketIO(app, cors_allowed_origins=cors_origins)
    app.config["SOCKETIO"] = socketio
    
    # Register root route before other routes
    @app.route("/", methods=["GET"])
    @app.route("/index.html", methods=["GET"])
    def index():
        """Serve main index.html from static folder (Production only).
        
        In development, Vite Dev Server on port 3000 handles the UI.
        This route only serves static builds for production deployments.
        """
        return jsonify({
            "error": "Development mode detected",
            "message": "Use http://localhost:3000 for UI (Vite Dev Server)",
            "production_usage": "Set FLASK_ENV=production to serve static builds from this port"
        }), 400
    
    @app.route("/assets/<path:filename>", methods=["GET"])
    def serve_assets(filename):
        """Serve static assets (Production only)."""
        return jsonify({
            "error": "Development mode detected",
            "message": "Use http://localhost:3000 for assets (Vite Dev Server)"
        }), 400
    
    # Register agent config routes (Phase 5.5) - legacy API bridged to runtime settings
    register_agent_config_routes(app, ki_config_manager=ki_config_manager, project_root=project_root)
    register_settings_routes(app, project_root=project_root)
    
    # Register all other routes (Phase 2D unified router)
    register_routes(app)
    register_project_routes(app)
    register_server_management_routes(app)
    
    # Register WebSocket handlers
    register_websocket(app, socketio)
    
    return app, socketio


# ============================================================================
# Global App Instances (for WSGI/production deployment)
# ============================================================================

app, socketio = create_app()  # live mode: config refreshed per request


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point when run as module."""
    host, port = get_web_settings(app.config["KICLI_CONFIG"])
    app.logger.info(f"Starting kicli-web server on {host}:{port}")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()

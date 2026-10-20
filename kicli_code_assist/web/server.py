"""
Flask backend server for web IDE.

Serves REST API + WebSocket for real-time chat streaming.
Reads config from ki.yaml and logs to ~/dev_data/kicli-code-assist/log/
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Thread
from datetime import datetime
import traceback

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.logging_integration import _get_or_create_logger, _get_log_dir
from ki_core.config import ConfigManager


# ============================================================================
# Configuration & Setup
# ============================================================================

def get_config() -> Dict[str, Any]:
    """Load configuration from ki.yaml via ConfigManager."""
    try:
        config_manager = ConfigManager()
        config = config_manager.load()
        return config
    except Exception as e:
        logger = logging.getLogger("kicli-web")
        logger.error(f"Failed to load config: {e}")
        return {
            "web": {"host": "127.0.0.1", "port": 8000},
            "storage": {"log_dir": str(Path.home() / "dev_data" / "kicli-code-assist" / "log")},
        }


def create_app(config: Optional[Dict] = None) -> Flask:
    """Create and configure Flask app."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "kicli-web-dev-secret"
    
    if config is None:
        config = get_config()
    
    # Store config in app context
    app.config["KICLI_CONFIG"] = config
    app.config["CHAT_SESSION"] = ChatSession()
    app.config["ACTIVE_REQUESTS"] = {}
    
    # Setup logging
    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    
    logger = _get_or_create_logger("kicli-web", "kicli-web.log")
    app.logger = logger
    
    # Setup CORS
    cors_origins = config.get("web", {}).get("cors_origins", ["http://localhost:3000"])
    CORS(app, origins=cors_origins)
    
    # Setup WebSocket
    socketio = SocketIO(app, cors_allowed_origins=cors_origins)
    app.config["SOCKETIO"] = socketio
    
    return app, socketio


# ============================================================================
# REST Endpoints
# ============================================================================

def register_routes(app: Flask):
    """Register REST API endpoints."""
    
    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
        })
    
    @app.route("/api/config", methods=["GET"])
    def get_config_endpoint():
        """Return current configuration."""
        try:
            config = app.config["KICLI_CONFIG"]
            return jsonify({
                "web": config.get("web", {}),
                "storage": config.get("storage", {}),
                "llm": config.get("llm", {}),
            })
        except Exception as e:
            app.logger.error(f"Config endpoint error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chat", methods=["POST"])
    def submit_chat():
        """Submit chat message with optional files."""
        try:
            data = request.get_json() or {}
            message = data.get("message", "").strip()
            files = data.get("files", [])
            
            if not message:
                return jsonify({"error": "Message cannot be empty"}), 400
            
            # Create request ID
            request_id = str(uuid.uuid4())
            
            # Store request info for WebSocket updates
            app.config["ACTIVE_REQUESTS"][request_id] = {
                "status": "processing",
                "message": message,
                "files": files,
            }
            
            # Log the request
            app.logger.info(f"Chat request {request_id}: message={len(message)} chars, files={len(files)}")
            
            # Process asynchronously in thread
            def process_chat():
                try:
                    chat_session: ChatSession = app.config["CHAT_SESSION"]
                    
                    # Add files to session as context
                    for file_obj in files:
                        if "path" in file_obj and "content" in file_obj:
                            chat_session.add_file(file_obj["path"], file_obj["content"])
                    
                    # Get formatted messages for API
                    messages = chat_session.get_messages_for_api(message)
                    
                    app.logger.info(f"Request {request_id}: {len(messages)} messages prepared")
                    
                    # Call LLM (this will fail without AsyncOllamaClient, expected)
                    from ki_core.adapters import ProviderChain
                    provider_chain = ProviderChain.from_config(app.config["KICLI_CONFIG"])
                    
                    # For now, simulate streaming response
                    app.config["ACTIVE_REQUESTS"][request_id]["status"] = "streaming"
                    
                    response_text = "Mock response: AsyncOllamaClient not yet implemented. Please use OpenAI provider for testing."
                    
                    # Emit via WebSocket
                    socketio = app.config["SOCKETIO"]
                    socketio.emit(
                        "chat.response",
                        {
                            "request_id": request_id,
                            "type": "chunk",
                            "content": response_text,
                        },
                        room=request_id
                    )
                    
                    socketio.emit(
                        "chat.response",
                        {
                            "request_id": request_id,
                            "type": "complete",
                            "status": "success",
                        },
                        room=request_id
                    )
                    
                    app.config["ACTIVE_REQUESTS"][request_id]["status"] = "complete"
                    
                except Exception as e:
                    app.logger.error(f"Chat processing error {request_id}: {e}\n{traceback.format_exc()}")
                    socketio = app.config["SOCKETIO"]
                    socketio.emit(
                        "chat.response",
                        {
                            "request_id": request_id,
                            "type": "error",
                            "error": str(e),
                        },
                        room=request_id
                    )
                    app.config["ACTIVE_REQUESTS"][request_id]["status"] = "error"
            
            # Start processing in background thread
            thread = Thread(target=process_chat, daemon=True)
            thread.start()
            
            return jsonify({
                "request_id": request_id,
                "status": "processing",
            })
        
        except Exception as e:
            app.logger.error(f"Chat endpoint error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/logs", methods=["GET"])
    def get_logs():
        """Return recent log entries."""
        try:
            lines = int(request.args.get("lines", 100))
            level = request.args.get("level", "INFO").upper()
            
            log_dir = app.config["KICLI_CONFIG"].get("storage", {}).get("log_dir", "log")
            log_file = Path(log_dir) / "kicli-web.log"
            
            if not log_file.exists():
                return jsonify({"logs": []})
            
            with open(log_file, "r") as f:
                log_lines = f.readlines()
            
            # Return last N lines
            recent_logs = log_lines[-lines:]
            
            return jsonify({
                "logs": recent_logs,
                "total_lines": len(log_lines),
            })
        
        except Exception as e:
            app.logger.error(f"Logs endpoint error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/upload", methods=["POST"])
    def upload_file():
        """Upload file to chat context."""
        try:
            if "file" not in request.files:
                app.logger.warning("No file in request")
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files["file"]
            if file.filename == "":
                app.logger.warning("Empty filename")
                return jsonify({"error": "No filename"}), 400
            
            # Read file content
            try:
                content = file.read().decode("utf-8", errors="replace")
            except Exception as e:
                app.logger.error(f"Failed to read file: {e}")
                content = str(file.read())
            
            file_id = str(uuid.uuid4())
            
            # Add to session
            try:
                chat_session: ChatSession = app.config["CHAT_SESSION"]
                chat_session.add_file(file.filename, content)
            except Exception as e:
                app.logger.warning(f"Failed to add file to chat session: {e}")
                # Don't fail, just log it
            
            app.logger.info(f"File uploaded: {file.filename} ({len(content)} bytes)")
            
            return jsonify({
                "file_id": file_id,
                "path": file.filename,
                "size_bytes": len(content),
            })
        
        except Exception as e:
            app.logger.error(f"File upload error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/<file_id>", methods=["DELETE"])
    def delete_file(file_id: str):
        """Remove file from context."""
        try:
            # TODO: implement file tracking by ID
            app.logger.info(f"File deleted: {file_id}")
            return jsonify({"status": "deleted"})
        except Exception as e:
            app.logger.error(f"File delete error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/save", methods=["PUT"])
    def save_file():
        """Save file content to filesystem."""
        try:
            data = request.json or {}
            file_path = data.get("path", "").strip()
            content = data.get("content", "")
            
            if not file_path:
                return jsonify({"error": "No file path provided"}), 400
            
            # Resolve project root
            from pathlib import Path
            project_root = Path.cwd()
            full_path = project_root / file_path
            
            # Security: prevent directory traversal
            if not full_path.resolve().is_relative_to(project_root.resolve()):
                app.logger.warning(f"Attempted path traversal: {file_path}")
                return jsonify({"error": "Invalid file path"}), 403
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            app.logger.info(f"File saved: {file_path} ({len(content)} bytes)")
            
            return jsonify({
                "status": "saved",
                "path": file_path,
                "size_bytes": len(content),
                "timestamp": datetime.now().isoformat(),
            })
        
        except PermissionError:
            app.logger.error(f"Permission denied saving file: {file_path}")
            return jsonify({"error": "Permission denied"}), 403
        
        except Exception as e:
            app.logger.error(f"File save error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    # ============================================================================
    # Static Files (Option 1: single-port deployment)
    # ============================================================================
    
    static_dir = Path(__file__).parent / "static"
    
    @app.route("/", methods=["GET"])
    def serve_index():
        """Serve index.html (SPA root)."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return send_from_directory(static_dir, "index.html")
        return jsonify({"error": "Frontend not built. Run: npm run build && collect_static.sh"}), 404
    
    @app.route("/<path:filename>", methods=["GET"])
    def serve_static(filename: str):
        """Serve static files or fallback to index.html (SPA routing)."""
        file_path = static_dir / filename
        
        # Check if file exists in static/
        if file_path.exists() and file_path.is_file():
            return send_from_directory(static_dir, filename)
        
        # Fallback to index.html for client-side routing
        index_file = static_dir / "index.html"
        if index_file.exists():
            return send_from_directory(static_dir, "index.html")
        
        return jsonify({"error": "Not found"}), 404


# ============================================================================
# WebSocket Events
# ============================================================================

def register_websocket(app: Flask, socketio: SocketIO):
    """Register WebSocket event handlers."""
    
    @socketio.on("connect")
    def handle_connect():
        """Client connected."""
        app.logger.info(f"Client connected: {request.sid}")
        emit("connection_response", {"data": "Connected to kicli-web"})
    
    @socketio.on("disconnect")
    def handle_disconnect():
        """Client disconnected."""
        app.logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on("subscribe")
    def handle_subscribe(data):
        """Subscribe to channel (e.g., chat.response.{request_id})."""
        channel = data.get("channel", "")
        if channel:
            join_room(channel)
            app.logger.debug(f"Client subscribed to {channel}")
            emit("subscribe_response", {"channel": channel, "status": "ok"})
    
    @socketio.on("unsubscribe")
    def handle_unsubscribe(data):
        """Unsubscribe from channel."""
        channel = data.get("channel", "")
        if channel:
            leave_room(channel)
            app.logger.debug(f"Client unsubscribed from {channel}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point when run as module."""
    config = get_config()
    app, socketio = create_app(config)
    
    register_routes(app)
    register_websocket(app, socketio)
    
    # Start server
    web_config = config.get("web", {})
    host = web_config.get("host", "127.0.0.1")
    port = web_config.get("port", 8000)
    
    app.logger.info(f"Starting kicli-web server on {host}:{port}")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
        log_output=False,
    )


if __name__ == "__main__":
    main()

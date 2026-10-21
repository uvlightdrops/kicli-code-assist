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
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.logging_integration import _get_or_create_logger, _get_log_dir
from ki_core.config import ConfigManager
from ki_core.adapters import AsyncOpenAIClient, ProviderChain
from ki_core.core.models import ChatRequest, Message, Role, StreamEventType


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


def create_app(config: Optional[Dict] = None) -> tuple[Flask, SocketIO]:
    """Create and configure Flask app with SocketIO.
    
    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "kicli-web-dev-secret"
    
    if config is None:
        config = get_config()
    
    # Store config in app context
    app.config["KICLI_CONFIG"] = config
    
    # ThreadPoolExecutor for async operations
    app.config["EXECUTOR"] = ThreadPoolExecutor(max_workers=4)
    app.config["ACTIVE_REQUESTS"] = {}
    app.config["CHAT_SESSION"] = ChatSession()
    
    # Setup logging
    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    logger = _get_or_create_logger("kicli-web", "kicli-web.log")
    app.logger = logger
    
    # Setup CORS
    cors_origins = config.get("web", {}).get("cors_origins", ["http://localhost:3000"])
    CORS(app, origins=cors_origins)
    
    # Create SocketIO instance
    socketio = SocketIO(app, cors_allowed_origins=cors_origins)
    app.config["SOCKETIO"] = socketio
    
    return app, socketio


# ============================================================================
# Async Chat Processing
# ============================================================================

async def process_chat_async(request_id: str, message: str, files: list, 
                             chat_session: ChatSession, config: Dict,
                             socketio: SocketIO, app: Flask) -> None:
    """Async chat processing with LLM provider chain.
    
    Args:
        request_id: Unique request identifier
        message: User message text
        files: List of file objects {path, content}
        chat_session: ChatSession instance
        config: App configuration
        socketio: SocketIO instance for WebSocket emit
        app: Flask app instance
    """
    logger = logging.getLogger("kicli-web")
    
    try:
        # Add user message to session
        chat_session.add_message("user", message)
        
        # Add files to session as context
        for file_obj in files:
            if "path" in file_obj and "content" in file_obj:
                chat_session.add_file(file_obj["path"], file_obj["content"])
        
        # Get formatted messages for API
        messages = chat_session.get_messages_for_api()
        logger.info(f"Request {request_id}: {len(messages)} messages prepared")
        
        # Try to use LLM provider if configured
        try:
            # Extract OpenAI config from ki.yaml (nested under llm.providers.openai)
            llm_config = config.get("llm", {})
            providers = llm_config.get("providers", {})
            openai_config = providers.get("openai", {})
            api_key = openai_config.get("api_key")
            model = openai_config.get("model", "gpt-4o-mini")
            base_url = openai_config.get("base_url", "https://api.openai.com/v1")
            
            if api_key:
                # Create async OpenAI client
                client = AsyncOpenAIClient(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                )
                
                # Build ChatRequest for LLM
                chat_request = ChatRequest(
                    messages=[
                        Message(role=Role.USER if msg.get("role") == "user" else Role.ASSISTANT, 
                               content=msg.get("content", ""))
                        for msg in messages
                    ],
                    model=model,
                    temperature=0.7,
                )
                
                # Stream response from LLM
                logger.info(f"Request {request_id}: Streaming from OpenAI ({model})")
                socketio.emit("chat.response", {
                    "request_id": request_id,
                    "type": "status",
                    "content": f"🤖 Querying LLM: {model}...",
                }, room=request_id)
                
                response_text = ""
                chunk_count = 0
                
                async for stream_event in client.achat_stream(chat_request):
                    # Check if this is a content token
                    if stream_event.type == StreamEventType.TOKEN:
                        chunk = stream_event.text
                        response_text += chunk
                        chunk_count += 1
                        
                        # Emit chunk via WebSocket (real-time streaming)
                        socketio.emit("chat.response", {
                            "request_id": request_id,
                            "type": "chunk",
                            "content": chunk,
                        }, room=request_id)
                        
                        logger.debug(f"Request {request_id}: Chunk {chunk_count} ({len(chunk)} chars)")
                    
                    elif stream_event.type == StreamEventType.DONE:
                        logger.info(f"Request {request_id}: Stream completed")
                        break
                
                # Add assistant response to chat history
                chat_session.add_message("assistant", response_text)
                logger.info(f"Request {request_id}: Response complete ({len(response_text)} chars, {chunk_count} chunks)")
                
                # Emit completion
                socketio.emit("chat.response", {
                    "request_id": request_id,
                    "type": "complete",
                    "status": "success",
                }, room=request_id)
                
            else:
                # No API key configured - show error
                logger.warning(f"Request {request_id}: No OpenAI API key configured")
                error_msg = "❌ OpenAI API key not configured in ki.yaml. Please add openai.api_key to enable LLM."
                socketio.emit("chat.response", {
                    "request_id": request_id,
                    "type": "error",
                    "error": error_msg,
                }, room=request_id)
                
        except ImportError as e:
            # AsyncOpenAI not installed
            logger.error(f"Request {request_id}: ImportError: {e}")
            error_msg = f"❌ Missing dependency: {str(e)}. Install: pip install openai"
            socketio.emit("chat.response", {
                "request_id": request_id,
                "type": "error",
                "error": error_msg,
            }, room=request_id)
        
    except Exception as e:
        logger.error(f"Chat processing error {request_id}: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        socketio.emit("chat.response", {
            "request_id": request_id,
            "type": "error",
            "error": f"Error: {type(e).__name__}: {str(e)}",
        }, room=request_id)


def process_chat_sync(request_id: str, message: str, files: list,
                      app: Flask, socketio: SocketIO) -> None:
    """Synchronous wrapper for async chat processing.
    
    Runs async chat in new event loop in separate thread.
    """
    logger = logging.getLogger("kicli-web")
    
    try:
        chat_session = app.config["CHAT_SESSION"]
        config = app.config["KICLI_CONFIG"]
        
        # Create new event loop in thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                process_chat_async(
                    request_id=request_id,
                    message=message,
                    files=files,
                    chat_session=chat_session,
                    config=config,
                    socketio=socketio,
                    app=app,
                )
            )
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Sync wrapper error {request_id}: {e}\n{traceback.format_exc()}")
        socketio.emit("chat.response", {
            "request_id": request_id,
            "type": "error",
            "error": f"Error: {type(e).__name__}: {str(e)}",
        }, room=request_id)


# ============================================================================
# REST Endpoints
# ============================================================================

def register_routes(app: Flask):
    """Register all REST API routes."""
    
    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "kicli-web"}), 200
    
    @app.route("/api/config", methods=["GET"])
    def get_app_config():
        """Get app configuration (non-sensitive)."""
        try:
            config = app.config["KICLI_CONFIG"]
            llm_config = config.get("llm", {})
            providers = llm_config.get("providers", {})
            openai_config = providers.get("openai", {})
            ollama_config = providers.get("ollama", {})
            return jsonify({
                "web": config.get("web", {}),
                "openai": {"configured": bool(openai_config.get("api_key"))},
                "ollama": {"configured": bool(ollama_config.get("base_url"))},
            }), 200
        except Exception as e:
            app.logger.error(f"Config endpoint error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/project/files", methods=["GET"])
    def get_project_files():
        """Get project file tree structure (flat list for current directory)."""
        try:
            config = app.config["KICLI_CONFIG"]
            project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            
            # Get requested path from query parameter
            requested_path = request.args.get("path", "")
            target_path = (project_root / requested_path).resolve()
            
            # Security: ensure path is within project_root
            if not target_path.is_relative_to(project_root):
                return jsonify({"error": "Access denied: path outside project"}), 403
            
            if not target_path.is_dir():
                return jsonify({"error": "Path is not a directory"}), 400
            
            items = []
            try:
                for item in sorted(target_path.iterdir()):
                    if item.name.startswith("."):
                        continue
                    
                    if item.is_file():
                        items.append({
                            "type": "file",
                            "name": item.name,
                            "path": str(item.relative_to(project_root)),
                            "size_bytes": item.stat().st_size,
                        })
                    elif item.is_dir():
                        items.append({
                            "type": "folder",
                            "name": item.name,
                            "path": str(item.relative_to(project_root)),
                        })
            except PermissionError:
                return jsonify({"error": "Permission denied"}), 403
            
            return jsonify({"items": items}), 200
            
        except Exception as e:
            app.logger.error(f"Project files error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/<path:file_path>", methods=["GET"])
    def read_file(file_path):
        """Read file contents."""
        try:
            config = app.config["KICLI_CONFIG"]
            project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            full_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            if not full_path.is_relative_to(project_root):
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            if not full_path.is_file():
                return jsonify({"error": "File not found"}), 404
            
            content = full_path.read_text(errors="replace")
            return jsonify({
                "path": file_path,
                "content": content,
                "size": len(content),
            }), 200
            
        except Exception as e:
            app.logger.error(f"File read error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chat", methods=["POST"])
    def chat():
        """Chat endpoint with streaming response via WebSocket."""
        try:
            data = request.json or {}
            message = data.get("message", "")
            files = data.get("files", [])
            
            request_id = str(uuid.uuid4())
            app.logger.info(f"Chat request {request_id}: message={len(message)} chars, files={len(files)}")
            
            # Spawn thread to handle async chat
            socketio = app.config["SOCKETIO"]
            thread = Thread(
                target=process_chat_sync,
                args=(request_id, message, files, app, socketio),
                daemon=True,
            )
            thread.start()
            
            return jsonify({"request_id": request_id}), 202
            
        except Exception as e:
            app.logger.error(f"Chat endpoint error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500


# ============================================================================
# WebSocket Event Handlers
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
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()

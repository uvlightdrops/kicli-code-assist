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
    
    # Register root route before SocketIO takes over
    @app.route("/", methods=["GET"])
    @app.route("/index.html", methods=["GET"])
    def index():
        """Serve main index.html from static folder (Production only).
        
        In development, Vite Dev Server on port 3000 handles the UI.
        This route only serves static builds for production deployments.
        """
        # In development mode, redirect to Vite Dev Server
        return jsonify({
            "error": "Development mode detected",
            "message": "Use http://localhost:3000 for UI (Vite Dev Server)",
            "production_usage": "Set FLASK_ENV=production to serve static builds from this port"
        }), 400
    
    @app.route("/assets/<path:filename>", methods=["GET"])
    def serve_assets(filename):
        """Serve static assets (Production only).
        
        In development, Vite Dev Server handles asset serving.
        """
        return jsonify({
            "error": "Development mode detected",
            "message": "Use http://localhost:3000 for assets (Vite Dev Server)"
        }), 400
    
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
        # Note: files are passed directly in the message, not stored in session
        chat_session.add_message("user", message, include_context=bool(files))
        
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

    @app.route("/api/agent/route", methods=["POST"])
    def agent_route():
        """
        Smart agent router: dispatches user query to multiple agents based on intent.
        
        Always runs Explain + Metrics together.
        Optionally runs additional agents based on intent detection.
        
        Request:
        {
            "query": "Explain this module and show metrics",
            "file_path": "src/pipeline.py",
            "scope": "folder" | "project",
            "project": "ypipe"
        }
        
        Response:
        {
            "intent": "explain_with_metrics",
            "agents": [
                {"type": "explain", "result": {...}},
                {"type": "metrics", "result": {...}}
            ],
            "session_id": "abc123",
            "scope": "folder"
        }
        """
        try:
            data = request.json or {}
            query = data.get("query", "").strip()
            file_path = data.get("file_path", "").strip()
            scope = data.get("scope", "folder")  # folder | project
            project_path = data.get("project", "").strip()
            
            if not query:
                return jsonify({"error": "Missing 'query' parameter"}), 400
            if not file_path:
                return jsonify({"error": "Missing 'file_path' parameter"}), 400
            
            # Resolve project root
            if not project_path:
                config = app.config["KICLI_CONFIG"]
                project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            else:
                project_root = Path(project_path).resolve()
                try:
                    ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                    project_root.relative_to(ALLOWED_ROOT)
                except ValueError:
                    return jsonify({"error": "Access denied: path outside allowed root"}), 403
            
            # Construct and validate file path
            full_file_path = (project_root / file_path).resolve()
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            # Detect intent from query - determines which agents to run
            intent = "explain_with_metrics"  # default
            agents_to_run = ["explain", "metrics"]  # always run these two together
            
            # Simple heuristic intent detection (can be upgraded to LLM later)
            query_lower = query.lower()
            if any(w in query_lower for w in ["refactor", "improve", "optimize", "clean", "smell"]):
                agents_to_run.append("refactor")
                intent = "explain_with_refactor"
            if any(w in query_lower for w in ["depend", "import", "circular", "coupling"]):
                agents_to_run.append("dependencies")
                intent = "explain_with_dependencies"
            if any(w in query_lower for w in ["error", "bug", "issue", "fix", "suggest"]):
                agents_to_run.append("suggest")
                intent = "explain_with_suggestions"
            
            # Run agents directly (not via HTTP, for efficiency)
            results = []
            
            from kicli_code_assist.agent import ProgrammingAgent
            try:
                from kicli_code_assist.agent.metrics import CodeMetricsAnalyzer
            except ImportError:
                CodeMetricsAnalyzer = None
            try:
                from kicli_code_assist.agent.refactoring import RefactoringAnalyzer
            except ImportError:
                RefactoringAnalyzer = None
            try:
                from kicli_code_assist.agent.dependencies import DependencyAnalyzer
            except ImportError:
                DependencyAnalyzer = None
            
            if "explain" in agents_to_run:
                try:
                    agent = ProgrammingAgent(project_root)
                    result = agent.explain_code(file_path=full_file_path, line_no=None)
                    results.append({"type": "explain", "result": result})
                except Exception as e:
                    app.logger.warning(f"Explain agent failed: {e}")
                    results.append({"type": "explain", "result": {"status": "error", "error": str(e)}})
            
            if "metrics" in agents_to_run:
                try:
                    if CodeMetricsAnalyzer:
                        analyzer = CodeMetricsAnalyzer(project_root=project_root)
                        result = analyzer.analyze(file_path=full_file_path)
                        results.append({"type": "metrics", "result": result})
                    else:
                        raise ImportError("CodeMetricsAnalyzer not available")
                except Exception as e:
                    app.logger.warning(f"Metrics agent failed: {e}")
                    results.append({"type": "metrics", "result": {"status": "error", "error": str(e)}})
            
            if "refactor" in agents_to_run:
                try:
                    if RefactoringAnalyzer:
                        analyzer = RefactoringAnalyzer(project_root=project_root)
                        result = analyzer.analyze(file_path=full_file_path)
                        results.append({"type": "refactor", "result": result})
                    else:
                        raise ImportError("RefactoringAnalyzer not available")
                except Exception as e:
                    app.logger.warning(f"Refactor agent failed: {e}")
                    results.append({"type": "refactor", "result": {"status": "error", "error": str(e)}})
            
            if "dependencies" in agents_to_run:
                try:
                    if DependencyAnalyzer:
                        analyzer = DependencyAnalyzer(project_root=project_root)
                        result = analyzer.analyze(file_path=full_file_path)
                        results.append({"type": "dependencies", "result": result})
                    else:
                        raise ImportError("DependencyAnalyzer not available")
                except Exception as e:
                    app.logger.warning(f"Dependencies agent failed: {e}")
                    results.append({"type": "dependencies", "result": {"status": "error", "error": str(e)}})
            
            if "suggest" in agents_to_run:
                try:
                    agent = ProgrammingAgent(project_root)
                    result = agent.suggest_refactoring(file_path=full_file_path)
                    results.append({"type": "suggest", "result": result})
                except Exception as e:
                    app.logger.warning(f"Suggest agent failed: {e}")
                    results.append({"type": "suggest", "result": {"status": "error", "error": str(e)}})
            
            # Generate session ID for follow-ups
            session_id = str(uuid.uuid4())
            
            return jsonify({
                "intent": intent,
                "agents": results,
                "session_id": session_id,
                "scope": scope,
            }), 200
            
        except Exception as e:
            app.logger.error(f"Agent route error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    # Helper function for resolving project root
    def resolve_project_root(project_path: Optional[str] = None) -> tuple[Path, Optional[str]]:
        """
        Resolve project root path from project parameter or config fallback.
        
        Returns:
            Tuple of (resolved project path, error message if any)
        """
        if not project_path or not project_path.strip():
            # Fallback to config
            config = app.config["KICLI_CONFIG"]
            return Path(config.get("storage", {}).get("project_root", ".")).resolve(), None
        
        # Use provided project path
        project_root = Path(project_path.strip()).resolve()
        
        # Verify path is safe (within /home/flow/dev_flow)
        try:
            ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
            project_root.relative_to(ALLOWED_ROOT)
            return project_root, None
        except ValueError:
            return None, "Access denied: path outside allowed root"
    
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
            # Get requested path from query parameter
            requested_path = request.args.get("path", "").strip()
            
            # Get the active project from query or fallback to config
            project_path = request.args.get("project", "").strip()
            
            if not project_path:
                # Fallback to config for backwards compatibility
                config = app.config["KICLI_CONFIG"]
                project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            else:
                # Use provided project path
                project_root = Path(project_path).resolve()
                
                # Verify path is safe (within /home/flow/dev_flow)
                try:
                    ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                    project_root.relative_to(ALLOWED_ROOT)
                except ValueError:
                    return jsonify({"error": "Access denied: path outside allowed root"}), 403
            
            target_path = (project_root / requested_path).resolve()
            
            # Security: ensure path is within project_root
            try:
                target_path.relative_to(project_root)
            except ValueError:
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
            # Get project from query parameter
            project_path = request.args.get("project", "").strip()
            
            if not project_path:
                # Fallback to config
                config = app.config["KICLI_CONFIG"]
                project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            else:
                # Use provided project path
                project_root = Path(project_path).resolve()
                
                # Verify path is safe (within /home/flow/dev_flow)
                try:
                    ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                    project_root.relative_to(ALLOWED_ROOT)
                except ValueError:
                    return jsonify({"error": "Access denied: path outside allowed root"}), 403
            
            full_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_path.relative_to(project_root)
            except ValueError:
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
    
    @app.route("/api/agent/explain", methods=["POST"])
    def agent_explain():
        """Agent: Explain code at specific file/line."""
        try:
            from kicli_code_assist.agent import ProgrammingAgent
            
            data = request.json or {}
            file_path = data.get("file")
            line_no = data.get("line")
            project_path = data.get("project", "").strip()
            
            if not file_path:
                return jsonify({"error": "Missing 'file' parameter"}), 400
            
            if not project_path:
                # Fallback to config
                config = app.config["KICLI_CONFIG"]
                project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            else:
                # Use provided project path
                project_root = Path(project_path).resolve()
                
                # Verify path is safe (within /home/flow/dev_flow)
                try:
                    ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                    project_root.relative_to(ALLOWED_ROOT)
                except ValueError:
                    return jsonify({"error": "Access denied: path outside allowed root"}), 403
            
            # Construct absolute file path
            full_file_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            # Initialize agent with project root
            agent = ProgrammingAgent(project_root)
            
            # Get explanation
            result = agent.explain_code(
                file_path=full_file_path,
                line_no=line_no,
            )
            
            return jsonify(result), 200 if result.get("status") == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent explain error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500
    
    @app.route("/api/agent/suggest", methods=["POST"])
    def agent_suggest():
        """Agent: Suggest refactorings for a file."""
        try:
            from kicli_code_assist.agent import ProgrammingAgent
            
            data = request.json or {}
            file_path = data.get("file")
            project_path = data.get("project", "").strip()
            
            if not file_path:
                return jsonify({"error": "Missing 'file' parameter"}), 400
            
            if not project_path:
                # Fallback to config
                config = app.config["KICLI_CONFIG"]
                project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            else:
                # Use provided project path
                project_root = Path(project_path).resolve()
                
                # Verify path is safe (within /home/flow/dev_flow)
                try:
                    ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                    project_root.relative_to(ALLOWED_ROOT)
                except ValueError:
                    return jsonify({"error": "Access denied: path outside allowed root"}), 403
            
            # Construct absolute file path
            full_file_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            # Initialize agent with project root
            agent = ProgrammingAgent(project_root)
            
            # Get suggestions
            result = agent.suggest_refactoring(
                file_path=full_file_path,
            )
            
            return jsonify(result), 200 if result.get("status") == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent suggest error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/agent/reason", methods=["POST"])
    def agent_reason():
        """Agent: Multi-step reasoning about code."""
        try:
            from kicli_code_assist.agent.reasoning import ReasoningAgent
            
            data = request.json or {}
            file_path = data.get("file")
            query = data.get("query", "How can this code be improved?")
            request_id = data.get("request_id", str(uuid.uuid4()))
            project_path = data.get("project", "").strip()
            
            if not file_path:
                return jsonify({"error": "Missing 'file' parameter"}), 400
            
            project_root, error = resolve_project_root(project_path)
            if error:
                return jsonify({"error": error}), 403
            
            # Construct absolute file path
            full_file_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            # Initialize reasoning agent
            agent = ReasoningAgent(project_root)
            
            # Run reasoning (sync wrapper for async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    agent.reason_about_code(
                        file_path=full_file_path,
                        query=query,
                        request_id=request_id,
                    )
                )
            finally:
                loop.close()
            
            return jsonify(result.to_dict()), 200 if result.status == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent reason error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/agent/ensemble", methods=["POST"])
    def agent_ensemble():
        """Agent: LLM ensemble voting (OpenAI + Ollama)."""
        try:
            from kicli_code_assist.agent.ensemble import LLMEnsemble
            
            data = request.json or {}
            code_snippet = data.get("code", "")
            question = data.get("question", "What is this code doing?")
            project_path = data.get("project", "").strip()
            request_id = data.get("request_id", str(uuid.uuid4()))
            
            if not code_snippet:
                return jsonify({"error": "Missing 'code' parameter"}), 400
            
            project_root, error = resolve_project_root(project_path)
            if error:
                return jsonify({"error": error}), 403
            
            # Initialize ensemble
            ensemble = LLMEnsemble(project_root)
            
            # Run ensemble voting (sync wrapper for async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    ensemble.vote_on_code(
                        code_snippet=code_snippet,
                        question=question,
                        request_id=request_id,
                    )
                )
            finally:
                loop.close()
            
            return jsonify(result.to_dict()), 200 if result.status == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent ensemble error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/agent/dependencies", methods=["POST"])
    def agent_dependencies():
        """Agent: Analyze dependencies and imports for a file or directory."""
        try:
            from kicli_code_assist.agent.dependencies import DependencyAnalyzer
            
            data = request.json or {}
            path = data.get("path")
            is_dir = data.get("is_dir", False)
            project_path = data.get("project", "").strip()
            
            if not path:
                return jsonify({"error": "Missing 'path' parameter"}), 400
            
            project_root, error = resolve_project_root(project_path)
            if error:
                return jsonify({"error": error}), 403
            
            # Construct absolute path
            full_path = (project_root / path).resolve()
            
            # Security: ensure path is within project_root
            try:
                full_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: path outside project"}), 403
            
            # Initialize dependency analyzer
            analyzer = DependencyAnalyzer(project_root)
            
            # Run analysis (sync wrapper for async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if is_dir:
                    graph = loop.run_until_complete(
                        analyzer.analyze_directory(full_path)
                    )
                else:
                    graph = loop.run_until_complete(
                        analyzer.analyze_file(full_path)
                    )
            finally:
                loop.close()
            
            return jsonify(graph.to_dict()), 200 if graph.status == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent dependencies error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/agent/refactor", methods=["POST"])
    def agent_refactor():
        """Agent: Suggest refactorings for a file."""
        try:
            from kicli_code_assist.agent.refactoring import RefactoringAnalyzer
            
            data = request.json or {}
            file_path = data.get("file")
            project_path = data.get("project", "").strip()
            
            if not file_path:
                return jsonify({"error": "Missing 'file' parameter"}), 400
            
            project_root, error = resolve_project_root(project_path)
            if error:
                return jsonify({"error": error}), 403
            
            # Construct absolute file path
            full_file_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            # Initialize refactoring analyzer
            analyzer = RefactoringAnalyzer(project_root)
            
            # Run analysis (sync wrapper for async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    analyzer.analyze_file(full_file_path)
                )
            finally:
                loop.close()
            
            return jsonify(result.to_dict()), 200 if result.status == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent refactor error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/agent/metrics", methods=["POST"])
    def agent_metrics():
        """Agent: Analyze code metrics for a file."""
        try:
            from kicli_code_assist.agent.metrics import CodeMetricsAnalyzer
            
            data = request.json or {}
            file_path = data.get("file")
            project_path = data.get("project", "").strip()
            
            if not file_path:
                return jsonify({"error": "Missing 'file' parameter"}), 400
            
            project_root, error = resolve_project_root(project_path)
            if error:
                return jsonify({"error": error}), 403
            
            # Construct absolute file path
            full_file_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            # Initialize metrics analyzer
            analyzer = CodeMetricsAnalyzer(project_root)
            
            # Run analysis (sync wrapper for async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    analyzer.analyze_file(full_file_path)
                )
            finally:
                loop.close()
            
            return jsonify(result.to_dict()), 200 if result.status == "ok" else 500
            
        except Exception as e:
            app.logger.error(f"Agent metrics error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/agent/stream-reason", methods=["POST"])
    def agent_stream_reason():
        """Agent: Reasoning with WebSocket streaming for real-time thinking steps."""
        try:
            from kicli_code_assist.agent.streaming import StreamingReasoningAgent
            
            data = request.json or {}
            file_path = data.get("file")
            query = data.get("query", "How can this code be improved?")
            project_path = data.get("project", "").strip()
            request_id = data.get("request_id", str(uuid.uuid4()))
            
            if not file_path:
                return jsonify({"error": "Missing 'file' parameter"}), 400
            
            project_root, error = resolve_project_root(project_path)
            if error:
                return jsonify({"error": error}), 403
            
            # Construct absolute file path
            full_file_path = (project_root / file_path).resolve()
            
            # Security: ensure file is within project_root
            try:
                full_file_path.relative_to(project_root)
            except ValueError:
                return jsonify({"error": "Access denied: file outside project"}), 403
            
            socketio = app.config["SOCKETIO"]
            
            # Spawn thread to handle async streaming
            def stream_reasoning():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    agent = StreamingReasoningAgent(project_root)
                    
                    def on_step(step):
                        """Emit step via WebSocket."""
                        socketio.emit(
                            "reasoning:step_complete",
                            {
                                "request_id": request_id,
                                "step": step.__dict__,
                            },
                            room=f"reasoning:{request_id}",
                        )
                    
                    # Run reasoning with streaming callback
                    result = loop.run_until_complete(
                        agent.reason_about_code_streaming(
                            file_path=full_file_path,
                            query=query,
                            request_id=request_id,
                            on_step_complete=on_step,
                        )
                    )
                    
                    # Emit final result
                    socketio.emit(
                        "reasoning:complete",
                        {
                            "request_id": request_id,
                            "result": result.to_dict(),
                        },
                        room=f"reasoning:{request_id}",
                    )
                finally:
                    loop.close()
            
            thread = Thread(target=stream_reasoning, daemon=True)
            thread.start()
            
            return jsonify({"request_id": request_id, "status": "streaming"}), 202
            
        except Exception as e:
            app.logger.error(f"Stream reason error: {e}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "error": str(e)}), 500

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
# Project Management Endpoints
# ============================================================================

def register_project_routes(app: Flask):
    """Register project management REST API routes."""
    
    ALLOWED_ROOT = Path("/home/flow/dev_flow")
    
    def is_safe_path(path_str: str) -> bool:
        """Verify path is within allowed root."""
        try:
            path = Path(path_str).resolve()
            return str(path).startswith(str(ALLOWED_ROOT.resolve()))
        except (ValueError, OSError):
            return False
    
    def load_project_metadata(project_path: str) -> Optional[Dict[str, Any]]:
        """Load or create project metadata."""
        path = Path(project_path)
        metadata_file = path / ".kicli_project"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                app.logger.warning(f"Failed to load project metadata: {e}")
        
        # Create new metadata
        return {
            "id": str(uuid.uuid4()),
            "name": path.name,
            "path": str(path.resolve()),
            "createdAt": datetime.now().isoformat(),
            "lastOpened": datetime.now().isoformat(),
            "type": "mixed",
            "isGitRepo": (path / ".git").exists(),
        }
    
    def save_project_metadata(project_path: str, metadata: Dict[str, Any]) -> None:
        """Save project metadata."""
        path = Path(project_path)
        metadata_file = path / ".kicli_project"
        metadata["lastOpened"] = datetime.now().isoformat()
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    @app.route("/api/projects/current", methods=["GET"])
    def get_current_project():
        """Get currently open project."""
        try:
            # For now, return null - project state managed in frontend
            return jsonify({"success": True, "data": None}), 200
        except Exception as e:
            app.logger.error(f"Get current project error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route("/api/projects/open", methods=["POST"])
    def open_project():
        """Open a project by path."""
        try:
            data = request.json or {}
            path = data.get("path", "").strip()
            
            if not path:
                return jsonify({"success": False, "error": "Path required"}), 400
            
            if not is_safe_path(path):
                return jsonify({
                    "success": False, 
                    "error": f"Path must be within {ALLOWED_ROOT}"
                }), 403
            
            project_path = Path(path).resolve()
            if not project_path.exists():
                return jsonify({
                    "success": False,
                    "error": "Project path does not exist"
                }), 404
            
            if not project_path.is_dir():
                return jsonify({
                    "success": False,
                    "error": "Path must be a directory"
                }), 400
            
            # Load/create metadata
            metadata = load_project_metadata(str(project_path))
            save_project_metadata(str(project_path), metadata)
            
            app.logger.info(f"Project opened: {project_path}")
            
            return jsonify({
                "success": True,
                "data": metadata
            }), 200
            
        except Exception as e:
            app.logger.error(f"Open project error: {e}\n{traceback.format_exc()}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route("/api/projects/create", methods=["POST"])
    def create_project():
        """Create a new project."""
        try:
            data = request.json or {}
            name = data.get("name", "").strip()
            parent_path = data.get("parentPath", str(ALLOWED_ROOT)).strip()
            template = data.get("template", "empty")
            
            if not name:
                return jsonify({"success": False, "error": "Project name required"}), 400
            
            if not is_safe_path(parent_path):
                return jsonify({
                    "success": False,
                    "error": f"Parent path must be within {ALLOWED_ROOT}"
                }), 403
            
            parent = Path(parent_path).resolve()
            if not parent.exists():
                return jsonify({
                    "success": False,
                    "error": "Parent path does not exist"
                }), 404
            
            # Create project directory
            project_path = parent / name
            if project_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Project already exists: {project_path}"
                }), 409
            
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create template structure
            if template == "node":
                (project_path / "package.json").write_text(json.dumps({
                    "name": name,
                    "version": "0.1.0",
                    "description": "",
                    "main": "index.js",
                    "scripts": {"start": "node index.js"},
                }, indent=2))
                (project_path / ".gitignore").write_text("node_modules/\n.env\n")
            elif template == "python":
                (project_path / ".gitignore").write_text("__pycache__/\n.venv/\n.env\n")
                (project_path / "requirements.txt").write_text("")
            
            # Create .gitignore for empty template too
            if not (project_path / ".gitignore").exists():
                (project_path / ".gitignore").write_text(".DS_Store\n")
            
            # Create metadata
            metadata = {
                "id": str(uuid.uuid4()),
                "name": name,
                "path": str(project_path.resolve()),
                "createdAt": datetime.now().isoformat(),
                "lastOpened": datetime.now().isoformat(),
                "type": "mixed",
                "isGitRepo": False,
            }
            save_project_metadata(str(project_path), metadata)
            
            app.logger.info(f"Project created: {project_path}")
            
            return jsonify({
                "success": True,
                "data": metadata
            }), 201
            
        except Exception as e:
            app.logger.error(f"Create project error: {e}\n{traceback.format_exc()}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route("/api/projects/browse", methods=["GET"])
    def browse_projects():
        """Browse folders for project selection."""
        try:
            path = request.args.get("path", str(ALLOWED_ROOT)).strip()
            
            if not is_safe_path(path):
                return jsonify({
                    "success": False,
                    "error": f"Path must be within {ALLOWED_ROOT}"
                }), 403
            
            folder = Path(path).resolve()
            if not folder.exists() or not folder.is_dir():
                return jsonify({"items": []}), 200
            
            # List only folders
            items = []
            try:
                for item in sorted(folder.iterdir()):
                    if item.is_dir() and not item.name.startswith("."):
                        items.append({
                            "name": item.name,
                            "path": str(item.resolve()),
                            "isFolder": True,
                        })
            except PermissionError:
                pass
            
            return jsonify({"items": items}), 200
            
        except Exception as e:
            app.logger.error(f"Browse projects error: {e}")
            return jsonify({"items": []}), 200
    
    @app.route("/api/projects/recent", methods=["GET"])
    def get_recent_projects():
        """Get recently opened projects from cache."""
        try:
            recent_file = ALLOWED_ROOT / ".kicli_recent_projects"
            recent = []
            
            if recent_file.exists():
                try:
                    with open(recent_file, "r") as f:
                        recent_data = json.load(f)
                        # Filter to existing projects
                        for proj in recent_data:
                            proj_path = Path(proj.get("path", ""))
                            if proj_path.exists():
                                recent.append(proj)
                except Exception as e:
                    app.logger.debug(f"Failed to load recent projects: {e}")
            
            return jsonify({"recent": recent[:10]}), 200
            
        except Exception as e:
            app.logger.error(f"Get recent projects error: {e}")
            return jsonify({"recent": []}), 200


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
    
    @socketio.on("reasoning:subscribe")
    def handle_reasoning_subscribe(data):
        """Subscribe to reasoning stream for a request_id."""
        request_id = data.get("request_id", "")
        if request_id:
            room = f"reasoning:{request_id}"
            join_room(room)
            app.logger.debug(f"Client subscribed to {room}")
            emit("reasoning:subscribed", {"request_id": request_id})
    
    @socketio.on("reasoning:unsubscribe")
    def handle_reasoning_unsubscribe(data):
        """Unsubscribe from reasoning stream."""
        request_id = data.get("request_id", "")
        if request_id:
            room = f"reasoning:{request_id}"
            leave_room(room)
            app.logger.debug(f"Client unsubscribed from {room}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point when run as module."""
    config = get_config()
    app, socketio = create_app(config)
    
    register_routes(app)
    register_project_routes(app)
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

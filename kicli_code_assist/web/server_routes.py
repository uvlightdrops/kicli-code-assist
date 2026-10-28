"""REST API endpoints for the web IDE.

Includes:
- Phase 2D: Intelligent Agent Router (/api/agent/route)  
- Project Management: File browser, analysis (/api/project/*)
- Streaming endpoints for reasoning and metrics
"""

import os
import logging
import json
import uuid
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_socketio import SocketIO

from kicli_code_assist.agent.meta_coordinator import (
    MetaCoordinationAgent, CoordinationRequest, get_meta_coordinator
)


logger = logging.getLogger("kicli-web")


def register_routes(app: Flask):
    """Register all REST API routes."""
    
    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "kicli-web"}), 200

    @app.route("/api/agent/route", methods=["POST"])
    def agent_route():
        """
        Phase 5.1: Intelligent Agent Router with MetaCoordinationAgent
        
        Uses MetaCoordinationAgent to orchestrate analysis and implementation workflows.
        
        Request:
        {
            "query": "Explain this file and show me metrics",
            "file_path": "/path/to/file.py",
            "project_root": "/path/to/project",
            "scope": "folder" or "project",
            "session_id": "optional-session-uuid"
        }
        
        Response (Success):
        {
            "success": true,
            "session_id": "session-uuid",
            "query": "...",
            "answer": "Detailed conversational response...",
            "intent": {
                "type": "explain",
                "confidence": 0.92
            },
            "workflow": "analysis",
            "agents_used": ["metrics", "refactoring", "dependencies"],
            "tabs": {
                "Structure": {...},
                "Metrics": {...},
                "Dependencies": {...}
            },
            "actions": [...],
            "timing": {
                "intent_ms": 123,
                "execution_ms": 456,
                "aggregation_ms": 789,
                "answer_ms": 234
            }
        }
        """
        import uuid
        import traceback
        
        session_id = None
        
        try:
            data = request.get_json() or {}
            query = data.get("query", "").strip()
            file_path = data.get("file_path", "").strip()
            project_root_str = data.get("project_root", "").strip()
            scope = data.get("scope", "project")
            session_id = data.get("session_id") or str(uuid.uuid4())
            
            # Validation
            if not query:
                return jsonify({
                    "success": False,
                    "error": "Missing 'query' parameter",
                    "session_id": session_id
                }), 400
            
            # file_path is optional for external project queries
            # Only required for file-specific analysis
            is_external_project_query = project_root_str and project_root_str != str(Path.cwd())
            if not is_external_project_query and not file_path:
                return jsonify({
                    "success": False,
                    "error": "Missing 'file_path' parameter",
                    "session_id": session_id
                }), 400
            
            # Resolve project_root
            if not project_root_str:
                config = app.config.get("KICLI_CONFIG", {})
                project_root = Path(config.get("storage", {}).get("project_root", ".")).resolve()
            else:
                project_root = Path(project_root_str).resolve()
                try:
                    ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                    project_root.relative_to(ALLOWED_ROOT)
                except ValueError:
                    return jsonify({
                        "success": False,
                        "error": "Access denied: path outside allowed root",
                        "session_id": session_id
                    }), 403
            
            # Resolve and validate file path
            file_path_obj = (
                Path(file_path).resolve() 
                if Path(file_path).is_absolute() 
                else (project_root / file_path).resolve()
            )
            try:
                file_path_obj.relative_to(project_root)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Access denied: file outside project",
                    "session_id": session_id
                }), 403
            
            logger.info(f"[{session_id}] Agent route: query='{query[:50]}' file={file_path_obj.name}")
            
            # Create coordination request
            coord_req = CoordinationRequest(
                query=query,
                file_path=str(file_path_obj),
                project_root=str(project_root),
                scope=scope,
                session_id=session_id
            )
            
            # Execute coordination
            coordinator = get_meta_coordinator()
            coord_result = coordinator.coordinate(coord_req)
            
            # Build response
            response = {
                "success": coord_result.success,
                "session_id": session_id,
                "query": coord_result.query,
                "answer": coord_result.answer,
                "intent": {
                    "type": coord_result.intent.get("type", "unknown") if isinstance(coord_result.intent, dict) else coord_result.intent.type,
                    "confidence": coord_result.intent.get("confidence", 0.0) if isinstance(coord_result.intent, dict) else coord_result.intent.confidence
                },
                "workflow": coord_result.workflow,
                "agents_used": coord_result.agents_used,
                "tabs": coord_result.tabs,
                "actions": coord_result.actions,
                "timing": coord_result.timing_ms
            }
            
            if coord_result.error:
                response["error"] = coord_result.error
            
            logger.info(
                f"[{session_id}] Complete: workflow={coord_result.workflow} "
                f"agents={coord_result.agents_used}"
            )
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"[{session_id}] Agent route error: {e}\n{traceback.format_exc()}")
            return jsonify({
                "success": False,
                "error": str(e),
                "session_id": session_id or "unknown"
            }), 500
    
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
            
            # Get requested path from query parameter (defaults to project root)
            requested_path = request.args.get("path", "").strip()
            
            # Build target path - if no path specified, use project root
            if requested_path:
                target_path = (project_root / requested_path).resolve()
            else:
                target_path = project_root
            
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

    @app.route("/api/agent/implement", methods=["POST"])
    def agent_implement():
        """
        Phase 5.5.2: Autonomous Implementation via HTTP
        
        Triggers CodeImplementationAgent to autonomously implement changes
        in an external project with Git workflow, testing, and state tracking.
        
        Request:
        {
            "query": "Description of what to implement",
            "project_root": "/path/to/project",
            "dry_run": false (optional, default: false)
        }
        
        Response:
        {
            "success": true,
            "session_id": "uuid",
            "status": "in_progress" | "completed" | "failed",
            "implementation_id": "uuid",
            "steps": [
                {"name": "Analysis", "status": "completed", "result": "..."},
                {"name": "Code Generation", "status": "in_progress", "result": null},
                ...
            ],
            "details": {...}
        }
        """
        try:
            from kicli_code_assist.agent.code_implementation import CodeImplementationAgent
            
            data = request.get_json() or {}
            query = data.get("query", "").strip()
            project_root_str = data.get("project_root", "").strip()
            dry_run = data.get("dry_run", False)
            
            if not query:
                return jsonify({"error": "query is required"}), 400
            
            if not project_root_str:
                return jsonify({"error": "project_root is required"}), 400
            
            project_root = Path(project_root_str).resolve()
            
            # Security check
            try:
                ALLOWED_ROOT = Path("/home/flow/dev_flow").resolve()
                project_root.relative_to(ALLOWED_ROOT)
            except ValueError:
                return jsonify({"error": "Access denied: path outside allowed root"}), 403
            
            if not project_root.exists():
                return jsonify({"error": f"Project path does not exist: {project_root}"}), 404
            
            # Create session
            session_id = str(uuid.uuid4())
            implementation_id = str(uuid.uuid4())
            
            # Initialize agent
            agent = CodeImplementationAgent(project_root=project_root)
            
            # Analyze project structure
            logger.info(f"[{session_id}] Starting autonomous implementation")
            logger.info(f"  Query: {query}")
            logger.info(f"  Project: {project_root}")
            
            steps = [
                {"name": "Project Analysis", "status": "in_progress", "result": None}
            ]
            
            # Step 1: Discover and analyze project
            try:
                agent.discover_python_files()
                agent.read_and_analyze_files()
                steps[0]["status"] = "completed"
                steps[0]["result"] = f"Found {len(agent.project_structure.main_modules)} modules, {len(agent.project_structure.python_files)} files"
            except Exception as e:
                steps[0]["status"] = "failed"
                steps[0]["result"] = str(e)
                logger.error(f"Project analysis failed: {e}", exc_info=True)
                return jsonify({
                    "success": False,
                    "session_id": session_id,
                    "implementation_id": implementation_id,
                    "status": "failed",
                    "steps": steps,
                    "error": str(e)
                }), 500
            
            # Step 2: Generate implementation code
            steps.append({"name": "Code Generation", "status": "in_progress", "result": None})
            try:
                generated_code = agent.generate_code_via_llm(
                    goal_title="Autonomous Implementation",
                    goal_description=query,
                    requirements=[]
                )
                steps[-1]["status"] = "completed"
                steps[-1]["result"] = f"Generated {len(str(generated_code.code)) if generated_code else 0} chars"
            except Exception as e:
                steps[-1]["status"] = "failed"
                steps[-1]["result"] = str(e)
                logger.error(f"Code generation failed: {e}", exc_info=True)
                return jsonify({
                    "success": False,
                    "session_id": session_id,
                    "implementation_id": implementation_id,
                    "status": "failed",
                    "steps": steps,
                    "error": str(e)
                }), 500
            
            # Step 3: Verify generated code
            steps.append({"name": "Code Verification", "status": "in_progress", "result": None})
            try:
                if not generated_code:
                    raise ValueError("LLM not configured or returned no code. Configure OpenAI or Ollama in ki.yaml")
                
                verification = generated_code.verify_implementation()
                if not verification["valid"]:
                    raise ValueError(f"Code verification failed: {verification.get('errors', [])}")
                steps[-1]["status"] = "completed"
                steps[-1]["result"] = "Code syntax and imports validated"
            except Exception as e:
                steps[-1]["status"] = "failed"
                steps[-1]["result"] = str(e)
                logger.error(f"Verification failed: {e}")
                return jsonify({
                    "success": False,
                    "session_id": session_id,
                    "implementation_id": implementation_id,
                    "status": "failed",
                    "steps": steps,
                    "error": str(e),
                    "details": {
                        "note": "LLM provider not configured",
                        "config_file": "ki.yaml (llm.providers.openai.api_key or llm.providers.ollama.base_url)"
                    }
                }), 500
            
            # Step 4: Apply code with full autonomy (git + tests + quality + state)
            steps.append({"name": "Code Application & Git Workflow", "status": "in_progress", "result": None})
            try:
                if dry_run:
                    # Dry run: just apply to disk, don't git
                    apply_result = agent.apply_generated_code(
                        generated_code,
                        dry_run=True
                    )
                    steps[-1]["result"] = f"Dry run: {apply_result.get('message', 'No changes')}"
                else:
                    # Full autonomy: git + tests + quality + state tracking
                    result = agent.apply_with_full_autonomy(
                        generated_code,
                        goal_description=query
                    )
                    steps[-1]["result"] = result
                
                steps[-1]["status"] = "completed"
                
            except Exception as e:
                steps[-1]["status"] = "failed"
                steps[-1]["result"] = str(e)
                logger.error(f"Application/Git workflow failed: {e}", exc_info=True)
                return jsonify({
                    "success": False,
                    "session_id": session_id,
                    "implementation_id": implementation_id,
                    "status": "failed",
                    "steps": steps,
                    "error": str(e)
                }), 500
            
            logger.info(f"[{session_id}] Autonomous implementation completed successfully")
            
            return jsonify({
                "success": True,
                "session_id": session_id,
                "implementation_id": implementation_id,
                "status": "completed",
                "steps": steps,
                "details": {
                    "project_root": str(project_root),
                    "query": query,
                    "dry_run": dry_run
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Autonomous implementation error: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500


# ============================================================================
# Server Management Endpoints (Phase 1)
# ============================================================================

def register_server_management_routes(app: Flask):
    """Register server management REST API routes."""
    from ki_core.server_management import ServiceRegistry, OrphanDetector

    @app.route("/api/server/status", methods=["GET"])
    def get_server_status():
        """Get status of all registered services."""
        try:
            registry = ServiceRegistry()
            services = registry.to_dict()
            
            return jsonify({
                "success": True,
                "services": services,
                "counts": {
                    "running": len(registry.get_running_services()),
                    "orphaned": len(registry.get_orphaned_services()),
                    "total": len(registry.list_services()),
                },
            }), 200
        except Exception as e:
            logger.error(f"Server status error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/server/detect-orphans", methods=["POST"])
    def detect_orphans():
        """Detect and mark orphaned services."""
        try:
            registry = ServiceRegistry()
            detector = OrphanDetector(registry)
            orphans = detector.detect_orphans()
            
            return jsonify({
                "success": True,
                "orphaned_count": len(orphans),
                "orphans": orphans,
            }), 200
        except Exception as e:
            logger.error(f"Orphan detection error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/server/cleanup", methods=["POST"])
    def cleanup_orphans():
        """Clean up orphaned services from registry."""
        try:
            registry = ServiceRegistry()
            detector = OrphanDetector(registry)
            result = detector.cleanup_orphans()
            
            return jsonify({
                "success": True,
                "cleaned": result['cleaned'],
                "services": result['services'],
            }), 200
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/server/register", methods=["POST"])
    def register_service():
        """Register a service."""
        try:
            data = request.json or {}
            name = data.get("name", "").strip()
            pid = data.get("pid")
            port = data.get("port")
            
            if not name or pid is None:
                return jsonify({
                    "error": "Missing 'name' or 'pid'"
                }), 400
            
            registry = ServiceRegistry()
            entry = registry.register(
                name=name,
                pid=pid,
                port=port,
                metadata=data.get("metadata")
            )
            
            return jsonify({
                "success": True,
                "service": {
                    "name": entry.name,
                    "pid": entry.pid,
                    "port": entry.port,
                    "status": entry.status,
                    "started_at": entry.started_at,
                },
            }), 201
        except Exception as e:
            logger.error(f"Service registration error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/server/unregister", methods=["POST"])
    def unregister_service():
        """Unregister a service."""
        try:
            data = request.json or {}
            name = data.get("name", "").strip()
            
            if not name:
                return jsonify({"error": "Missing 'name'"}), 400
            
            registry = ServiceRegistry()
            success = registry.unregister(name)
            
            return jsonify({
                "success": success,
                "message": f"Service '{name}' {'unregistered' if success else 'not found'}",
            }), 200 if success else 404
        except Exception as e:
            logger.error(f"Service unregistration error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


# ============================================================================
# WebSocket Event Handlers
# ============================================================================


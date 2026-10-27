"""REST API endpoints for the web IDE.

Includes:
- Phase 2D: Intelligent Agent Router (/api/agent/route)  
- Project Management: File browser, analysis (/api/project/*)
- Streaming endpoints for reasoning and metrics
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_socketio import SocketIO

from kicli_code_assist.web.server_instances import (
    get_intent_detector, get_executor, get_aggregator, get_answer_generator
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
        Phase 2D: Intelligent Agent Router with Parallel Execution
        
        Integrates Phase 2A (Intent Detection), Phase 2B (Parallel Execution),
        and Phase 2C (Result Aggregation) into a single endpoint.
        
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
            "intent": {
                "type": "EXPLAIN",
                "confidence": 0.92,
                "agents": ["explain", "metrics"]
            },
            "summary": "Natural language summary from Phase 2C...",
            "tabs": {
                "Structure": {...},
                "Metrics": {...}
            },
            "actions": [],
            "next_steps": ["Add type hints", "Optimize loop"],
            "timing": {
                "intent_ms": 1200,
                "execution_ms": 350,
                "aggregation_ms": 800,
                "total_ms": 2350
            }
        }
        """
        async def _agent_route_async():
            """Async implementation of agent_route."""
            session_id = None
            total_start = time.time()
            
            try:
                data = request.get_json() or {}
                query = data.get("query", "").strip()
                file_path = data.get("file_path", "").strip()
                project_root_str = data.get("project_root", "").strip()
                scope = data.get("scope", "folder")
                session_id = data.get("session_id") or str(uuid.uuid4())
                
                # Validation
                if not query:
                    return jsonify({"success": False, "error": "Missing 'query' parameter", "session_id": session_id}), 400
                if not file_path:
                    return jsonify({"success": False, "error": "Missing 'file_path' parameter", "session_id": session_id}), 400
                
                # Resolve project_root
                if not project_root_str:
                    config = app.config["KICLI_CONFIG"]
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
                file_path_obj = Path(file_path).resolve() if Path(file_path).is_absolute() else (project_root / file_path).resolve()
                try:
                    file_path_obj.relative_to(project_root)
                except ValueError:
                    return jsonify({
                        "success": False,
                        "error": "Access denied: file outside project",
                        "session_id": session_id
                    }), 403
                
                app.logger.info(f"[{session_id}] Processing query: '{query}' on {file_path_obj.name}")
                
                # Phase 2A: Detect Intent
                intent_start = time.time()
                intent_detector = get_intent_detector()
                agent_intent = await intent_detector.detect_intent(
                    query,
                    file_context={"file": str(file_path_obj), "scope": scope}
                )
                intent_ms = (time.time() - intent_start) * 1000
                app.logger.info(
                    f"[{session_id}] Intent: {agent_intent.intent_type.value} "
                    f"(confidence: {agent_intent.confidence:.2f}) → agents: {agent_intent.agents_to_run}"
                )
                
                # Phase 2B: Execute Agents in Parallel
                executor_start = time.time()
                executor = get_executor(project_root)
                executor_result = await executor.execute(
                    query=query,
                    file_path=file_path_obj,
                    scope=scope,
                    session_id=session_id
                )
                execution_ms = (time.time() - executor_start) * 1000
                app.logger.info(f"[{session_id}] Execution complete: {execution_ms:.1f}ms")
                
                # Phase 2C: Aggregate Results
                aggregation_start = time.time()
                aggregator = get_aggregator()
                aggregated = await aggregator.aggregate(
                    executor_result=executor_result,
                    file_path=file_path_obj,
                    query=query
                )
                aggregation_ms = (time.time() - aggregation_start) * 1000
                app.logger.info(f"[{session_id}] Aggregation complete: {aggregation_ms:.1f}ms")
                
                # Phase 2E: Generate Conversational Answer
                answer_start = time.time()
                answer_generator = get_answer_generator()
                analysis_context = AnalysisContext(
                    query=query,
                    file_path=str(file_path_obj),
                    structure=aggregated.tabs['Structure'].data if 'Structure' in aggregated.tabs else None,
                    metrics=aggregated.tabs['Metrics'].data if 'Metrics' in aggregated.tabs else None,
                    dependencies=aggregated.tabs['Dependencies'].data if 'Dependencies' in aggregated.tabs else None,
                    refactor_suggestions=aggregated.tabs['Refactor'].data if 'Refactor' in aggregated.tabs else None,
                )
                answer = await answer_generator.generate_answer(query, analysis_context)
                answer_ms = (time.time() - answer_start) * 1000
                app.logger.info(f"[{session_id}] Answer generation complete: {answer_ms:.1f}ms")
                
                # Calculate total timing
                total_ms = (time.time() - total_start) * 1000
                
                # Build response
                response = {
                    "success": True,
                    "session_id": session_id,
                    "query": query,
                    "answer": answer,
                    "intent": {
                        "type": agent_intent.intent_type.value,
                        "confidence": agent_intent.confidence,
                        "agents": agent_intent.agents_to_run,
                        "reasoning": agent_intent.reasoning
                    },
                    "summary": aggregated.summary,
                    "tabs": {name: tab.to_dict() for name, tab in aggregated.tabs.items()},
                    "actions": [action.to_dict() for action in aggregated.actions],
                    "next_steps": aggregated.next_steps,
                    "timing": {
                        "intent_ms": round(intent_ms, 1),
                        "execution_ms": round(execution_ms, 1),
                        "aggregation_ms": round(aggregation_ms, 1),
                        "answer_ms": round(answer_ms, 1),
                        "total_ms": round(total_ms, 1)
                    },
                    "synthesis_method": aggregated.synthesis_method
                }
                
                app.logger.info(f"[{session_id}] Response complete: {total_ms:.1f}ms total")
                return jsonify(response), 200
                
            except Exception as e:
                app.logger.error(f"[{session_id}] Agent route error: {e}\n{traceback.format_exc()}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "session_id": session_id
                }), 500
        
        # Run async implementation using event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_agent_route_async())
        finally:
            loop.close()
    
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


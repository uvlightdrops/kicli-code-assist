"""WebSocket handlers for real-time communication.

Handles:
- Chat messaging (chat:send, chat:subscribe)
- Reasoning stream subscriptions (reasoning:subscribe)
- Agent execution streaming (agent:execution namespace)
- Token counting and response streaming

Phase 5.5.2.I2: Enhanced WebSocket streaming with execution lifecycle management
"""

import logging
from typing import Optional, Dict, Any
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from kicli_code_assist.web.server_instances import (
    get_intent_detector, get_executor, get_aggregator, get_answer_generator
)


logger = logging.getLogger("kicli-web")

# Track active execution subscriptions
_EXECUTION_SUBSCRIPTIONS: Dict[str, set] = {}  # execution_id → {sid, ...}


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
    
    # ========================================================================
    # Agent Execution Namespace: /agent/execution
    # ========================================================================
    # Real-time event streaming for CodeImplementationAgent transparency
    
    @socketio.on("subscribe:execution", namespace="/agent/execution")
    def handle_execution_subscribe(data):
        """Subscribe to execution events.
        
        Args:
            data: {"execution_id": str}
        """
        execution_id = data.get("execution_id", "")
        if not execution_id:
            emit("error", {"message": "execution_id required"})
            return
        
        room = f"execution:{execution_id}"
        join_room(room)
        
        # Track subscription
        if execution_id not in _EXECUTION_SUBSCRIPTIONS:
            _EXECUTION_SUBSCRIPTIONS[execution_id] = set()
        _EXECUTION_SUBSCRIPTIONS[execution_id].add(request.sid)
        
        # Get execution manager to validate session exists
        from kicli_code_assist.web.execution_manager import get_execution_manager
        try:
            manager = get_execution_manager()
            session = manager.get_session(execution_id)
            
            if session:
                emit("agent:subscribed", {
                    "execution_id": execution_id,
                    "status": "subscribed",
                    "session_status": session.status,
                    "events_so_far": session.event_count
                })
                app.logger.debug(f"Client {request.sid} subscribed to execution {execution_id}")
            else:
                emit("error", {
                    "message": f"Execution {execution_id} not found",
                    "execution_id": execution_id
                })
        
        except RuntimeError:
            # ExecutionManager not initialized (e.g., in tests)
            emit("agent:subscribed", {
                "execution_id": execution_id,
                "status": "subscribed"
            })
            app.logger.debug(f"Client {request.sid} subscribed to execution {execution_id}")
    
    @socketio.on("unsubscribe:execution", namespace="/agent/execution")
    def handle_execution_unsubscribe(data):
        """Unsubscribe from execution events.
        
        Args:
            data: {"execution_id": str}
        """
        execution_id = data.get("execution_id", "")
        if not execution_id:
            return
        
        room = f"execution:{execution_id}"
        leave_room(room)
        
        # Track unsubscription
        if execution_id in _EXECUTION_SUBSCRIPTIONS:
            _EXECUTION_SUBSCRIPTIONS[execution_id].discard(request.sid)
            if not _EXECUTION_SUBSCRIPTIONS[execution_id]:
                del _EXECUTION_SUBSCRIPTIONS[execution_id]
        
        app.logger.debug(f"Client unsubscribed from execution {execution_id}")
        emit("agent:unsubscribed", {
            "execution_id": execution_id,
            "status": "unsubscribed"
        })
    
    @socketio.on("get:execution_status", namespace="/agent/execution")
    def handle_execution_status(data):
        """Get current execution status.
        
        Args:
            data: {"execution_id": str}
        """
        execution_id = data.get("execution_id", "")
        if not execution_id:
            emit("error", {"message": "execution_id required"})
            return
        
        # TODO: Look up status from ExecutionManager
        # For now, return basic status
        status = {
            "execution_id": execution_id,
            "status": "running",
            "total_events": 0,
            "active_subscribers": len(_EXECUTION_SUBSCRIPTIONS.get(execution_id, set()))
        }
        
        emit("agent:status", status)
    
    @socketio.on("connect", namespace="/agent/execution")
    def handle_execution_connect():
        """Client connected to /agent/execution namespace."""
        app.logger.debug(f"Client connected to /agent/execution: {request.sid}")
        emit("connection_response", {
            "namespace": "/agent/execution",
            "data": "Connected to agent execution namespace"
        })
    
    @socketio.on("disconnect", namespace="/agent/execution")
    def handle_execution_disconnect():
        """Client disconnected from /agent/execution namespace."""
        app.logger.debug(f"Client disconnected from /agent/execution: {request.sid}")
        
        # Clean up subscriptions for this SID
        for execution_id in list(_EXECUTION_SUBSCRIPTIONS.keys()):
            _EXECUTION_SUBSCRIPTIONS[execution_id].discard(request.sid)
            if not _EXECUTION_SUBSCRIPTIONS[execution_id]:
                del _EXECUTION_SUBSCRIPTIONS[execution_id]


# ============================================================================

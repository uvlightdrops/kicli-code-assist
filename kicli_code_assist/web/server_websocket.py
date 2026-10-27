"""WebSocket handlers for real-time communication.

Handles:
- Chat messaging (chat:send, chat:subscribe)
- Reasoning stream subscriptions (reasoning:subscribe)
- Token counting and response streaming
"""

import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from kicli_code_assist.web.server_instances import (
    get_intent_detector, get_executor, get_aggregator, get_answer_generator
)


logger = logging.getLogger("kicli-web")


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

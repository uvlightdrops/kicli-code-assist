"""Asynchronous processing for chat and streaming.

Handles:
- Async LLM integration with streaming
- Event loop management in Flask context
- Token counting and response aggregation
"""

import asyncio
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from flask import Flask, request
from flask_socketio import SocketIO

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.web.server_instances import (
    get_intent_detector, get_executor, get_aggregator, get_answer_generator
)
from ki_core.core.models import ChatRequest, Message, Role, StreamEventType

from kicli_code_assist.llm_runtime import resolve_chat


logger = logging.getLogger("kicli-web")


def run_async_in_executor(executor: ThreadPoolExecutor, coro):
    """Run async coroutine in ThreadPoolExecutor.
    
    This is a workaround for running async code in Flask's sync context.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


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
        
        # Build the client from the configuration of *this* request
        # (llm.provider incl. ki/openai/ollama/mock/auto, endpoint, model,
        # http.request_timeout/verify_ssl) - see kicli_code_assist.llm_runtime.
        try:
            client, settings = resolve_chat(config)
        except Exception as e:
            logger.warning(f"Request {request_id}: LLM not configured ({type(e).__name__})")
            socketio.emit("chat.response", {
                "request_id": request_id,
                "type": "error",
                "error": f"❌ LLM not configured: {e}. Adjust llm.* in the settings panel; "
                         "API keys belong in creds.yaml.",
            }, room=request_id)
            return

        provider, model = settings.get("provider"), settings.get("model")
        role_map = {"user": Role.USER, "assistant": Role.ASSISTANT, "system": Role.SYSTEM}
        chat_request = ChatRequest(
            messages=[
                Message(role=role_map.get(msg.get("role"), Role.USER), content=msg.get("content", ""))
                for msg in messages
            ],
            model=model,
            temperature=0.7,
        )

        logger.info(f"Request {request_id}: Streaming from {provider} ({model})")
        socketio.emit("chat.response", {
            "request_id": request_id,
            "type": "status",
            "content": f"🤖 Querying LLM: {provider}/{model}...",
        }, room=request_id)

        response_text = ""
        chunk_count = 0
        try:
            async for stream_event in client.achat_stream(chat_request):
                if stream_event.type == StreamEventType.TOKEN and stream_event.text:
                    response_text += stream_event.text
                    chunk_count += 1
                    socketio.emit("chat.response", {
                        "request_id": request_id,
                        "type": "chunk",
                        "content": stream_event.text,
                    }, room=request_id)
                elif stream_event.type == StreamEventType.DONE:
                    break
        except Exception as e:
            logger.error(f"Request {request_id}: LLM error from {provider}: {type(e).__name__}")
            socketio.emit("chat.response", {
                "request_id": request_id,
                "type": "error",
                "error": f"❌ LLM error ({provider}): {type(e).__name__}: {e}",
            }, room=request_id)
            return

        chat_session.add_message("assistant", response_text)
        logger.info(f"Request {request_id}: Response complete ({len(response_text)} chars, {chunk_count} chunks)")
        socketio.emit("chat.response", {
            "request_id": request_id,
            "type": "complete",
            "status": "success",
            "provider": provider,
            "model": model,
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


"""Asynchronous processing for chat and streaming.

Handles:
- Async LLM integration with streaming
- Event loop management in Flask context
- Token counting and response aggregation
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from flask import request
from flask_socketio import SocketIO

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.web.server_instances import (
    get_intent_detector, get_executor, get_aggregator, get_answer_generator
)
from ki_core.adapters import AsyncOpenAIClient
from ki_core.core.models import ChatRequest, Message, Role, StreamEventType


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


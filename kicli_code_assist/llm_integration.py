"""Async LLM integration for ChatSession.

Bridges between ChatSession (sync) and async LLM providers.
Handles error conversion and recovery hints.
Supports token-by-token streaming with cancellation.
"""

import asyncio
import logging
from typing import Optional, Callable
import json

from ki_core.adapters import ProviderChain
from ki_core.adapters.openai_async import AsyncOpenAIClient
from ki_core.core.models import ChatRequest, ChatResponse
from ki_core.errors import (
    KICoreError,
    LLMError,
    AllProvidersFailedError,
    ProviderConfigError,
)
from ki_core.security import SensitiveDataFilter

from kicli_code_assist.app_config import AppConfig
from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.streaming import (
    StreamCancellation,
    TokenCounter,
    StreamDisplayFormatter,
)

logger = logging.getLogger(__name__)

# Import LLM logger for detailed logging
try:
    from kicli_code_assist.logging_integration import get_llm_logger
    llm_logger = get_llm_logger()
except ImportError:
    llm_logger = logger


class AsyncLLMIntegration:
    """Async LLM integration for non-blocking AI operations."""

    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize async LLM integration.
        
        Args:
            config: AppConfig instance (uses default if not provided)
        """
        self.config = config or AppConfig.from_env()
        self.provider_chain: Optional[ProviderChain] = None
        self.secret_filter = SensitiveDataFilter()
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize provider chain with configured providers."""
        providers = []
        llm_logger.info("=" * 60)
        llm_logger.info("Initializing LLM providers")
        
        # Check if providers are actually configured
        openai_enabled = self.config.openai_api_key and not self.config.openai_api_key.startswith("${")
        # Ollama is enabled if base_url is set (includes localhost default)
        ollama_enabled = bool(self.config.ollama_base_url)
        
        llm_logger.info(f"OpenAI enabled: {openai_enabled}")
        llm_logger.info(f"Ollama enabled: {ollama_enabled}")

        # Try OpenAI if configured
        if openai_enabled:
            try:
                from ki_core.adapters.openai_async import AsyncOpenAIClient
                from ki_core.core.models import ChatRequest
                
                model = self.config.openai_model or "gpt-4o-mini"
                client = AsyncOpenAIClient(
                    api_key=self.config.openai_api_key,
                    model=model,
                    timeout=30,
                )
                providers.append(client)
                llm_logger.info(f"✓ OpenAI provider initialized")
                llm_logger.info(f"  Model: {model}")
            except Exception as e:
                llm_logger.warning(f"Failed to initialize OpenAI: {e}")

        # Try Ollama if explicitly configured
        if ollama_enabled:
            try:
                from ki_core.adapters.ollama import OllamaClient
                
                model = self.config.ollama_model or "llama3.2"
                client = OllamaClient(
                    base_url=self.config.ollama_base_url,
                    model=model,
                )
                providers.append(client)
                llm_logger.info(f"✓ Ollama provider initialized")
                llm_logger.info(f"  Base URL: {self.config.ollama_base_url}")
                llm_logger.info(f"  Model: {model}")
            except Exception as e:
                llm_logger.warning(f"Failed to initialize Ollama: {e}")

        # Fallback: If no providers configured, try Ollama on localhost
        if not providers:
            llm_logger.info("No providers explicitly configured, trying Ollama on localhost:11434...")
            try:
                from ki_core.adapters.ollama import OllamaClient
                
                model = self.config.ollama_model or "llama3.2"
                client = OllamaClient(
                    base_url="http://localhost:11434",
                    model=model,
                )
                providers.append(client)
                llm_logger.info(f"✓ Ollama fallback initialized (localhost:11434)")
                llm_logger.info(f"  Model: {model}")
                llm_logger.info("  NOTE: Using localhost fallback. To use different provider, set config values.")
            except Exception as e:
                llm_logger.warning(f"Failed to initialize Ollama fallback: {e}")

        if providers:
            self.provider_chain = ProviderChain(providers)
            llm_logger.info(f"Provider chain ready: {len(providers)} provider(s)")
        else:
            llm_logger.error("No LLM providers available (no config + Ollama localhost not responding)")

    async def query(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Query LLM asynchronously (non-blocking).
        
        Args:
            messages: List of chat messages
            system_prompt: Optional system prompt (will be filtered for secrets)
            on_progress: Optional callback for progress updates
            
        Returns:
            Response text from LLM
            
        Raises:
            AllProvidersFailedError: If all providers fail
            ProviderConfigError: If no providers configured
        """
        llm_logger.info("-" * 60)
        llm_logger.info("LLM Query Started")
        llm_logger.info(f"Message count: {len(messages)}")
        
        if not self.provider_chain:
            llm_logger.error("No provider chain configured")
            raise ProviderConfigError(
                "LLM",
                "No LLM providers configured. Set OPENAI_API_KEY or OLLAMA_BASE_URL."
            )

        # Log message content summary (with safety)
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            content_preview = content[:100] if isinstance(content, str) else str(content)[:100]
            llm_logger.info(f"  [{i}] {role}: {content_preview}{'...' if len(str(content)) > 100 else ''}")

        # Filter system prompt for secrets
        original_system = system_prompt
        if system_prompt:
            original_length = len(system_prompt)
            system_prompt = self.secret_filter.filter(system_prompt)
            redactions = self.secret_filter.get_redaction_count()
            if redactions > 0:
                llm_logger.warning(f"Filtered {redactions} secret(s) from system prompt")
                llm_logger.info(f"System prompt length: {original_length} → {len(system_prompt)} chars")

        # Build ChatRequest with model from active provider
        from ki_core.core.models import ChatRequest, Message, Role

        message_objs = [
            Message(role=Role(msg["role"]), content=msg["content"])
            for msg in messages
        ]
        
        # Use model from the configured provider
        model = None
        if self.config.openai_api_key:
            model = self.config.openai_model or "gpt-4o-mini"
        elif self.config.ollama_base_url:
            model = self.config.ollama_model or "llama3.2"
        else:
            model = "gpt-4o-mini"
        
        llm_logger.info(f"Active model: {model}")
        
        request = ChatRequest(
            messages=message_objs,
            model=model,
        )

        try:
            if on_progress:
                on_progress("Querying LLM...")
            
            llm_logger.info("Sending request to provider chain...")
            response = await self.provider_chain.achat(request)
            
            response_text = response.message.content
            response_length = len(response_text)
            llm_logger.info(f"Response received: {response_length} chars")
            llm_logger.info(f"Response preview: {response_text[:200]}{'...' if response_length > 200 else ''}")
            
            return response_text
            
        except LLMError as e:
            llm_logger.error(f"LLM error: {e.message}")
            if on_progress:
                on_progress(f"LLM Error: {e.message}")
            raise
        except Exception as e:
            llm_logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            import traceback
            llm_logger.error(f"Traceback:\n{traceback.format_exc()}")
            if on_progress:
                on_progress(f"Error: {type(e).__name__}: {e}")
            raise

    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
        on_token_count: Optional[Callable[[int], None]] = None,
        cancellation: Optional[StreamCancellation] = None,
    ) -> str:
        """Stream LLM response asynchronously with cancellation support.
        
        Args:
            messages: List of chat messages
            system_prompt: Optional system prompt (filtered for secrets)
            on_chunk: Callback for each response chunk
            on_progress: Callback for progress updates
            on_token_count: Callback for token count updates (called after each token)
            cancellation: Optional StreamCancellation to allow user to cancel mid-stream
            
        Returns:
            Complete response text (empty string if cancelled)
            
        Raises:
            AllProvidersFailedError: If all providers fail
            ProviderConfigError: If no providers configured
        """
        llm_logger.info("-" * 60)
        llm_logger.info("LLM Stream Started")
        llm_logger.info(f"Message count: {len(messages)}")
        
        if not self.provider_chain:
            llm_logger.error("No provider chain configured")
            raise ProviderConfigError(
                "LLM",
                "No LLM providers configured"
            )

        # Log message summaries
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            content_preview = content[:100] if isinstance(content, str) else str(content)[:100]
            llm_logger.info(f"  [{i}] {role}: {content_preview}{'...' if len(str(content)) > 100 else ''}")

        # Filter secrets
        if system_prompt:
            original_length = len(system_prompt)
            system_prompt = self.secret_filter.filter(system_prompt)
            redactions = self.secret_filter.get_redaction_count()
            if redactions > 0:
                llm_logger.warning(f"Filtered {redactions} secret(s) from system prompt")

        from ki_core.core.models import ChatRequest, Message, Role

        message_objs = [
            Message(role=Role(msg["role"]), content=msg["content"])
            for msg in messages
        ]
        
        request = ChatRequest(messages=message_objs)

        full_response = ""
        chunk_count = 0
        token_counter = TokenCounter()
        formatter = StreamDisplayFormatter()
        
        # Create cancellation context if not provided
        if cancellation is None:
            cancellation = StreamCancellation()
        
        try:
            if on_progress:
                on_progress("Streaming from LLM...")
            
            llm_logger.info("Starting stream from provider chain...")
            
            async for event in self.provider_chain.achat_stream(request):
                # Check if user requested cancellation
                if cancellation.cancelled:
                    llm_logger.warning("Stream cancelled by user")
                    if on_progress:
                        on_progress("Streaming cancelled")
                    break
                
                if event.text:
                    full_response += event.text
                    chunk_count += 1
                    
                    # Update token count
                    token_counter.add_token(event.text)
                    if on_token_count:
                        on_token_count(token_counter.get_count())
                    
                    # Format and display token
                    formatted_token = formatter.format_token(event.text)
                    
                    if on_chunk:
                        on_chunk(formatted_token)
                    
                    llm_logger.debug(f"Chunk {chunk_count}: {len(event.text)} chars → {token_counter.get_count()} tokens")
            
            final_token_count = token_counter.get_count()
            llm_logger.info(f"Stream complete: {len(full_response)} chars in {chunk_count} chunks ({final_token_count} tokens)")
            llm_logger.info(f"Response preview: {full_response[:200]}{'...' if len(full_response) > 200 else ''}")
            
            return full_response
            
        except LLMError as e:
            llm_logger.error(f"LLM streaming error: {e.message}")
            raise
        except Exception as e:
            llm_logger.error(f"Unexpected error during streaming: {type(e).__name__}: {e}")
            import traceback
            llm_logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise

    def get_stats(self) -> dict:
        """Get provider chain statistics.
        
        Returns:
            Dict with query/fallback stats
        """
        if self.provider_chain:
            return self.provider_chain.get_stats()
        return {}


# Global integration instance (lazy-loaded)
_integration: Optional[AsyncLLMIntegration] = None


def get_async_integration(config: Optional[AppConfig] = None) -> AsyncLLMIntegration:
    """Get or create global async LLM integration.
    
    Args:
        config: Optional config override
        
    Returns:
        AsyncLLMIntegration instance
    """
    global _integration
    if _integration is None:
        _integration = AsyncLLMIntegration(config)
    return _integration

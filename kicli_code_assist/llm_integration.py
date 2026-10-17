"""Async LLM integration for ChatSession.

Bridges between ChatSession (sync) and async LLM providers.
Handles error conversion and recovery hints.
"""

import asyncio
import logging
from typing import Optional, Callable

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

logger = logging.getLogger(__name__)


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

        # Try OpenAI if configured
        if self.config.openai_api_key:
            try:
                from ki_core.adapters.openai_async import AsyncOpenAIClient
                from ki_core.core.models import ChatRequest
                
                client = AsyncOpenAIClient(
                    api_key=self.config.openai_api_key,
                    model=self.config.llm_model or "gpt-4o-mini",
                    timeout=30,
                )
                providers.append(client)
                logger.info("✓ OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # Try Ollama if configured
        if self.config.ollama_base_url:
            try:
                from ki_core.adapters.openai_compat import OpenAICompatibleClient
                
                client = OpenAICompatibleClient(
                    base_url=self.config.ollama_base_url,
                    api_key="not-needed",  # Ollama doesn't require auth
                    model="llama2",
                )
                providers.append(client)
                logger.info("✓ Ollama provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama: {e}")

        if providers:
            self.provider_chain = ProviderChain(providers)
        else:
            logger.warning("No LLM providers configured!")

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
        if not self.provider_chain:
            raise ProviderConfigError(
                "LLM",
                "No LLM providers configured. Set OPENAI_API_KEY or OLLAMA_BASE_URL."
            )

        # Filter system prompt for secrets
        if system_prompt:
            original_length = len(system_prompt)
            system_prompt = self.secret_filter.filter(system_prompt)
            redactions = self.secret_filter.get_redaction_count()
            if redactions > 0:
                logger.info(f"Filtered {redactions} secret(s) from system prompt")

        # Build ChatRequest
        from ki_core.core.models import ChatRequest, Message, Role

        message_objs = [
            Message(role=Role(msg["role"]), content=msg["content"])
            for msg in messages
        ]
        
        request = ChatRequest(
            messages=message_objs,
            model=self.config.llm_model,
        )

        try:
            if on_progress:
                on_progress("Querying LLM...")
            
            response = await self.provider_chain.achat(request)
            return response.message.content
            
        except LLMError as e:
            logger.error(f"LLM error: {e.message}")
            # Re-raise with original error info
            raise
        except Exception as e:
            logger.error(f"Unexpected error during LLM query: {e}")
            raise

    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Stream LLM response asynchronously (non-blocking).
        
        Args:
            messages: List of chat messages
            system_prompt: Optional system prompt (filtered for secrets)
            on_chunk: Callback for each response chunk
            on_progress: Callback for progress updates
            
        Returns:
            Complete response text
            
        Raises:
            AllProvidersFailedError: If all providers fail
            ProviderConfigError: If no providers configured
        """
        if not self.provider_chain:
            raise ProviderConfigError(
                "LLM",
                "No LLM providers configured"
            )

        # Filter secrets
        if system_prompt:
            system_prompt = self.secret_filter.filter(system_prompt)

        from ki_core.core.models import ChatRequest, Message, Role

        message_objs = [
            Message(role=Role(msg["role"]), content=msg["content"])
            for msg in messages
        ]
        
        request = ChatRequest(messages=message_objs)

        full_response = ""
        
        try:
            if on_progress:
                on_progress("Streaming from LLM...")
            
            async for event in self.provider_chain.achat_stream(request):
                if event.text:
                    full_response += event.text
                    if on_chunk:
                        on_chunk(event.text)
            
            return full_response
            
        except LLMError as e:
            logger.error(f"LLM streaming error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
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

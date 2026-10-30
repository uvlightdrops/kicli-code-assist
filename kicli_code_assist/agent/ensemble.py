"""Ensemble LLM with OpenAI + Ollama voting and consensus."""

from __future__ import annotations

import asyncio
import time
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any

from ki_core.core.models import ChatRequest, Message, Role

from kicli_code_assist.llm_runtime import chat_client, current_config

@dataclass
class LLMResponse:
    """Single LLM response."""
    provider: str  # "openai" or "ollama"
    text: str
    duration_ms: int = 0
    tokens_used: int = 0
    error: Optional[str] = None


@dataclass
class VotingResult:
    """Result from LLM ensemble voting."""
    status: str = "ok"
    request_id: str = ""
    prompt: str = ""
    responses: List[LLMResponse] = field(default_factory=list)
    consensus: str = ""
    agreement_score: float = 0.0  # 0.0-1.0
    total_duration_ms: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


class LLMEnsemble:
    """Ensemble voting with OpenAI + Ollama."""

    def __init__(self, project_root: Path = Path("."), config: Optional[Dict[str, Any]] = None):
        """Initialize ensemble with the configuration current at request time."""
        self.project_root = project_root
        self.config = current_config() if config is None else config

    async def vote_on_code(
        self,
        code_snippet: str,
        question: str = "What is this code doing?",
        request_id: str = "",
    ) -> VotingResult:
        """
        Get OpenAI + Ollama responses and compute consensus.

        Args:
            code_snippet: Code to analyze
            question: Question to ask about code
            request_id: Request ID for tracking

        Returns:
            VotingResult with both responses and consensus
        """
        result = VotingResult(
            request_id=request_id,
            prompt=question,
        )

        start_time = time.time()

        try:
            # Build prompt
            prompt = f"""Question: {question}

Code:
```
{code_snippet[:2000]}  # Limit to 2000 chars
```

Please provide a concise analysis (2-3 sentences)."""

            # Parallel calls to both LLMs
            openai_task = self._call_openai(prompt)
            ollama_task = self._call_ollama(prompt)

            responses = await asyncio.gather(
                openai_task, ollama_task, return_exceptions=True
            )

            # Process OpenAI response
            if isinstance(responses[0], Exception):
                result.responses.append(
                    LLMResponse(
                        provider="openai",
                        text="",
                        error=str(responses[0]),
                    )
                )
            else:
                result.responses.append(responses[0])

            # Process Ollama response
            if isinstance(responses[1], Exception):
                result.responses.append(
                    LLMResponse(
                        provider="ollama",
                        text="",
                        error=str(responses[1]),
                    )
                )
            else:
                result.responses.append(responses[1])

            # Compute consensus if both responses succeeded
            successful_responses = [r for r in result.responses if not r.error]

            if len(successful_responses) == 2:
                result.consensus = self._compute_consensus(successful_responses)
                result.agreement_score = self._compute_agreement(successful_responses)
            elif len(successful_responses) == 1:
                result.consensus = successful_responses[0].text
                result.agreement_score = 0.5
            else:
                result.status = "error"
                result.error = "Both LLMs failed"

        except Exception as e:
            result.status = "error"
            result.error = str(e)

        finally:
            result.total_duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _call_provider(self, provider: str, prompt: str) -> LLMResponse:
        """One vote via ki-core's client (endpoint/model/timeout/TLS from config)."""
        start_time = time.time()
        try:
            client = chat_client(self.config, provider=provider)
            request = ChatRequest(
                messages=[Message(role=Role.USER, content=prompt)],
                temperature=0.3,
            )
            response = await client.achat(request)
            return LLMResponse(
                provider=provider,
                text=response.message.content,
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return LLMResponse(
                provider=provider,
                text="",
                duration_ms=int((time.time() - start_time) * 1000),
                error=f"{type(e).__name__}: {e}",
            )

    async def _call_openai(self, prompt: str) -> LLMResponse:
        """Call the configured OpenAI provider."""
        return await self._call_provider("openai", prompt)

    async def _call_ollama(self, prompt: str) -> LLMResponse:
        """Call the configured Ollama provider."""
        return await self._call_provider("ollama", prompt)

    def _compute_consensus(self, responses: List[LLMResponse]) -> str:
        """Simple consensus: return both if different, one if similar."""
        if len(responses) < 2:
            return responses[0].text if responses else ""

        openai_resp = next((r for r in responses if r.provider == "openai"), None)
        ollama_resp = next((r for r in responses if r.provider == "ollama"), None)

        if not openai_resp or not ollama_resp:
            return responses[0].text

        # Check similarity (simplified: common words)
        openai_words = set(openai_resp.text.lower().split())
        ollama_words = set(ollama_resp.text.lower().split())
        common = openai_words & ollama_words

        if len(common) > 10:  # Very similar
            return openai_resp.text
        else:  # Different perspectives
            return f"OpenAI: {openai_resp.text[:200]}...\n\nOllama: {ollama_resp.text[:200]}..."

    def _compute_agreement(self, responses: List[LLMResponse]) -> float:
        """Compute agreement score (0.0-1.0) based on response similarity."""
        if len(responses) < 2:
            return 0.0

        text1 = responses[0].text.lower()
        text2 = responses[1].text.lower()

        # Simple overlap metric
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        max_words = max(len(words1), len(words2))

        return overlap / max_words

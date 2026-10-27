"""LLM-based intent detection for agent routing (Phase 2A)."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Dict, List, Optional

from ki_core.core.models import ChatRequest, Message, Role

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """User intent categories for agent routing."""
    EXPLAIN = "explain"
    REFACTOR = "refactor"
    REVIEW = "review"
    OPTIMIZE = "optimize"
    DIAGNOSE = "diagnose"
    SUGGEST = "suggest"
    VALIDATE = "validate"


@dataclass
class AgentIntent:
    """Result of LLM-based intent classification.
    
    Attributes:
        intent_type: The classified intent category
        agents_to_run: List of agent names to execute (e.g., ["explain", "metrics"])
        confidence: Confidence score (0.0-1.0)
        reasoning: Explanation of why this classification was chosen
        additional_context: Optional metadata for the intent
    """
    
    intent_type: IntentType
    agents_to_run: List[str]
    confidence: float
    reasoning: str
    additional_context: Optional[Dict[str, str]] = None
    
    @property
    def is_confident(self) -> bool:
        """Returns True if confidence >= 0.75."""
        return self.confidence >= 0.75
    
    def to_dict(self) -> Dict:
        """Serialize intent to dictionary."""
        return {
            "intent_type": self.intent_type.value,
            "agents_to_run": self.agents_to_run,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "additional_context": self.additional_context,
        }


# Mapping of intent types to recommended agent lists
INTENT_TO_AGENTS: Dict[IntentType, List[str]] = {
    IntentType.EXPLAIN: ["explain", "metrics"],
    IntentType.REFACTOR: ["refactor", "suggest"],
    IntentType.REVIEW: ["review", "suggest"],
    IntentType.OPTIMIZE: ["metrics", "refactor"],
    IntentType.DIAGNOSE: ["explain", "metrics", "dependencies"],
    IntentType.SUGGEST: ["suggest", "metrics"],
    IntentType.VALIDATE: ["review", "dependencies"],
}

# Keyword fallback patterns for each intent
# More specific keywords with primary/exclusive terms first
INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
    IntentType.EXPLAIN: [
        "explain", "what does", "how does", "tell me", "describe", "understand",
        "clarify", "show me", "meaning", "purpose", "how it works",
    ],
    IntentType.REFACTOR: [
        "refactor", "simplify", "clean", "reorganize", "cleaner",
        "rewrite", "restructure", "code quality", "readable", "implementation",
    ],
    IntentType.REVIEW: [
        "review", "check", "audit", "examine", "look at",
        "validate", "verify", "issue", "problem", "quality",
    ],
    IntentType.OPTIMIZE: [
        "optimize", "optimization", "performance", "speed", "faster",
        "efficient", "efficiency", "memory", "resource", "slow",
    ],
    IntentType.DIAGNOSE: [
        "debug", "diagnose", "error", "exception", "crash", "crashing",
        "fail", "trace", "broken", "not working", "fix", "what's wrong", "wrong",
    ],
    IntentType.SUGGEST: [
        "suggest", "recommendation", "what if", "could", "should",
        "best practice", "pattern", "implement", "create", "build",
        "how do i", "how can i", "example",
    ],
    IntentType.VALIDATE: [
        "validate", "correct", "is this right", "check correctness",
        "test coverage", "dependencies", "imports", "dependency",
    ],
}


class AgentIntentDetector:
    """LLM-based intent detection with fallback to keyword matching.
    
    This detector uses an LLM (via ProviderChain) to classify user queries
    into intent categories that map to appropriate agents. Falls back to
    keyword matching if LLM is unavailable or fails.
    
    Uses query caching to avoid redundant LLM calls.
    """
    
    def __init__(self, provider_chain=None):
        """Initialize the intent detector.
        
        Args:
            provider_chain: Optional ProviderChain instance. If None, will be
                          initialized on first use.
        """
        self.provider_chain = provider_chain
        self._query_cache: Dict[str, AgentIntent] = {}
        self._max_cache_size = 256
    
    async def detect_intent(
        self,
        query: str,
        file_context: Optional[Dict] = None,
    ) -> AgentIntent:
        """Detect intent from user query.
        
        Args:
            query: User query (e.g., "Explain this function")
            file_context: Optional context dict with file info (e.g., {"file": "module.py"})
            
        Returns:
            AgentIntent with classification and recommended agents
        """
        # Check cache first
        cache_key = self._get_cache_key(query, file_context)
        if cache_key in self._query_cache:
            logger.debug(f"Intent cache hit for query: {query[:50]}...")
            return self._query_cache[cache_key]
        
        # Try LLM-based detection
        if self.provider_chain:
            try:
                intent = await self._detect_intent_llm(query, file_context)
                self._cache_intent(cache_key, intent)
                return intent
            except Exception as e:
                logger.warning(f"LLM intent detection failed: {e}, falling back to keywords")
        
        # Fallback to keyword matching
        intent = self._detect_intent_keywords(query)
        self._cache_intent(cache_key, intent)
        return intent
    
    async def _detect_intent_llm(
        self,
        query: str,
        file_context: Optional[Dict] = None,
    ) -> AgentIntent:
        """Use LLM to detect intent from query.
        
        Args:
            query: User query
            file_context: Optional file context
            
        Returns:
            AgentIntent from LLM classification
            
        Raises:
            Exception: If LLM call fails
        """
        if not self.provider_chain:
            raise ValueError("ProviderChain not initialized")
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Build user prompt
        user_prompt = self._build_user_prompt(query, file_context)
        
        # Call LLM
        request = ChatRequest(
            messages=[
                Message(role=Role.SYSTEM, content=system_prompt),
                Message(role=Role.USER, content=user_prompt),
            ],
            temperature=0.3,  # Deterministic classification
        )
        
        logger.debug(f"Calling LLM for intent detection: {query[:50]}...")
        response = await self.provider_chain.achat(request)
        
        # Parse response
        intent = self._parse_llm_response(response.message.content, query)
        return intent
    
    def _detect_intent_keywords(self, query: str) -> AgentIntent:
        """Fallback: detect intent using keyword matching.
        
        Args:
            query: User query
            
        Returns:
            AgentIntent from keyword classification
        """
        query_lower = query.lower()
        
        # Score each intent type
        scores: Dict[IntentType, float] = {intent_type: 0.0 for intent_type in IntentType}
        
        for intent_type, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[intent_type] += 1.0
        
        # Find best match
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 3.0, 1.0)  # Normalize to 0-1
        
        # Low confidence if no keywords matched
        if confidence == 0:
            best_intent = IntentType.SUGGEST
            confidence = 0.5
        
        agents = INTENT_TO_AGENTS[best_intent]
        reasoning = f"Keyword matching: detected '{best_intent.value}' from query"
        
        logger.debug(f"Keyword intent detection: {best_intent.value} (confidence: {confidence:.2f})")
        
        return AgentIntent(
            intent_type=best_intent,
            agents_to_run=agents,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _parse_llm_response(self, response_text: str, query: str) -> AgentIntent:
        """Parse LLM response into AgentIntent.
        
        Args:
            response_text: Raw LLM response (should be JSON)
            query: Original user query (for fallback)
            
        Returns:
            AgentIntent parsed from response
        """
        try:
            # Extract JSON from response (LLM may include extra text)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start < 0 or json_end <= json_start:
                logger.warning("No JSON found in LLM response, falling back to keywords")
                return self._detect_intent_keywords(query)
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate and extract fields
            intent_str = data.get("intent_type", "suggest").lower()
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "LLM classification")
            
            # Map string to IntentType
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                logger.warning(f"Unknown intent type: {intent_str}, using SUGGEST")
                intent_type = IntentType.SUGGEST
            
            # Get agents for this intent
            agents = INTENT_TO_AGENTS.get(intent_type, [intent_type.value])
            
            # Validate confidence
            confidence = max(0.0, min(1.0, confidence))
            
            logger.debug(
                f"LLM intent: {intent_type.value} (confidence: {confidence:.2f})"
            )
            
            return AgentIntent(
                intent_type=intent_type,
                agents_to_run=agents,
                confidence=confidence,
                reasoning=reasoning,
            )
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return self._detect_intent_keywords(query)
        except Exception as e:
            logger.exception(f"Error parsing LLM response: {e}")
            return self._detect_intent_keywords(query)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM intent classification."""
        intent_list = ", ".join([f"'{it.value}'" for it in IntentType])
        agents_list = ", ".join(
            [f"'{agent}'" for agents in INTENT_TO_AGENTS.values() for agent in agents]
        )
        
        return f"""You are an expert at understanding developer intent.
Classify the user's query into one of these intent categories: {intent_list}.

For each query, respond with a JSON object containing:
- intent_type: The primary intent (one of the above categories)
- confidence: Your confidence in this classification (0.0 to 1.0)
- reasoning: Brief explanation of why you chose this intent

Available agents to recommend: {agents_list}.

Guidelines:
- EXPLAIN: User wants to understand code, its purpose, or how it works
- REFACTOR: User wants to improve code structure or readability
- REVIEW: User wants code review, bug checking, or quality assessment
- OPTIMIZE: User wants to improve performance or efficiency
- DIAGNOSE: User wants to debug, trace, or fix errors
- SUGGEST: User wants recommendations or implementation help
- VALIDATE: User wants to verify correctness or test coverage

Be precise and confident. Use high confidence (0.8+) only when intent is very clear."""

    def _build_user_prompt(self, query: str, file_context: Optional[Dict] = None) -> str:
        """Build user prompt for intent classification.
        
        Args:
            query: The user's query
            file_context: Optional context about the file being analyzed
            
        Returns:
            Formatted user prompt
        """
        prompt = f"Query: {query}\n"
        
        if file_context:
            if "file" in file_context:
                prompt += f"File: {file_context['file']}\n"
            if "language" in file_context:
                prompt += f"Language: {file_context['language']}\n"
            if "summary" in file_context:
                prompt += f"File summary: {file_context['summary']}\n"
        
        prompt += "\nRespond with JSON only (no other text):"
        return prompt
    
    def _get_cache_key(self, query: str, file_context: Optional[Dict] = None) -> str:
        """Generate cache key from query and context.
        
        Args:
            query: User query
            file_context: Optional context dict
            
        Returns:
            Cache key string
        """
        # Use query as primary cache key
        key = query.lower().strip()
        
        # Include file name if available
        if file_context and "file" in file_context:
            key += f":{file_context['file']}"
        
        return key
    
    def _cache_intent(self, key: str, intent: AgentIntent) -> None:
        """Cache an intent result.
        
        Args:
            key: Cache key
            intent: AgentIntent to cache
        """
        # Simple LRU: if cache is full, clear oldest entry
        if len(self._query_cache) >= self._max_cache_size:
            # Remove first (oldest) entry
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
            logger.debug("Query cache full, evicted oldest entry")
        
        self._query_cache[key] = intent
    
    def clear_cache(self) -> None:
        """Clear the intent cache."""
        self._query_cache.clear()
        logger.info("Intent cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dict with cache size and max size
        """
        return {
            "cache_size": len(self._query_cache),
            "max_cache_size": self._max_cache_size,
        }


@lru_cache(maxsize=8)
def get_intent_detector(provider_chain=None) -> AgentIntentDetector:
    """Get or create a singleton intent detector.
    
    Args:
        provider_chain: Optional ProviderChain for LLM-based detection
        
    Returns:
        Singleton AgentIntentDetector instance
        
    Note:
        This is a module-level singleton with LRU caching.
        For testing, use AgentIntentDetector() directly.
    """
    return AgentIntentDetector(provider_chain=provider_chain)

"""Unit tests for AgentIntentDetector (Phase 2A)."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kicli_code_assist.agent.intent_detector import (
    AgentIntent,
    AgentIntentDetector,
    IntentType,
    INTENT_KEYWORDS,
    INTENT_TO_AGENTS,
)
from ki_core.core.models import ChatResponse, Message, Role


class TestIntentType:
    """Test IntentType enum."""
    
    def test_intent_types_exist(self):
        """Test all required intent types exist."""
        expected = {"EXPLAIN", "REFACTOR", "REVIEW", "OPTIMIZE", "DIAGNOSE", "SUGGEST", "VALIDATE"}
        actual = {member.name for member in IntentType}
        assert expected == actual
    
    def test_intent_type_values(self):
        """Test intent type values are lowercase."""
        for intent_type in IntentType:
            assert intent_type.value == intent_type.value.lower()


class TestAgentIntent:
    """Test AgentIntent dataclass."""
    
    def test_agent_intent_creation(self):
        """Test creating an AgentIntent."""
        intent = AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain", "metrics"],
            confidence=0.85,
            reasoning="User asked to explain the function",
        )
        
        assert intent.intent_type == IntentType.EXPLAIN
        assert intent.agents_to_run == ["explain", "metrics"]
        assert intent.confidence == 0.85
        assert intent.reasoning == "User asked to explain the function"
        assert intent.additional_context is None
    
    def test_is_confident_property(self):
        """Test is_confident property."""
        high_conf = AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.8,
            reasoning="test",
        )
        assert high_conf.is_confident is True
        
        low_conf = AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.5,
            reasoning="test",
        )
        assert low_conf.is_confident is False
        
        boundary = AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.75,
            reasoning="test",
        )
        assert boundary.is_confident is True
    
    def test_to_dict(self):
        """Test serializing intent to dict."""
        intent = AgentIntent(
            intent_type=IntentType.REFACTOR,
            agents_to_run=["refactor", "suggest"],
            confidence=0.9,
            reasoning="Improve code quality",
            additional_context={"language": "python"},
        )
        
        d = intent.to_dict()
        assert d["intent_type"] == "refactor"
        assert d["agents_to_run"] == ["refactor", "suggest"]
        assert d["confidence"] == 0.9
        assert d["reasoning"] == "Improve code quality"
        assert d["additional_context"] == {"language": "python"}


class TestIntentMapping:
    """Test intent to agent mappings."""
    
    def test_all_intents_mapped(self):
        """Test all intent types have agent mappings."""
        for intent_type in IntentType:
            assert intent_type in INTENT_TO_AGENTS
            agents = INTENT_TO_AGENTS[intent_type]
            assert len(agents) > 0
            assert all(isinstance(a, str) for a in agents)
    
    def test_all_intents_have_keywords(self):
        """Test all intent types have keyword patterns."""
        for intent_type in IntentType:
            assert intent_type in INTENT_KEYWORDS
            keywords = INTENT_KEYWORDS[intent_type]
            assert len(keywords) > 0
            assert all(isinstance(k, str) for k in keywords)


class TestAgentIntentDetectorKeywords:
    """Test keyword-based fallback intent detection."""
    
    def test_detect_explain_intent(self):
        """Test detecting EXPLAIN intent."""
        detector = AgentIntentDetector()
        
        queries = [
            "Explain this function",
            "What does this code do?",
            "Tell me about this class",
            "Describe how this works",
        ]
        
        for query in queries:
            intent = detector._detect_intent_keywords(query)
            assert intent.intent_type == IntentType.EXPLAIN
            assert "explain" in intent.agents_to_run
    
    def test_detect_refactor_intent(self):
        """Test detecting REFACTOR intent."""
        detector = AgentIntentDetector()
        
        queries = [
            "Refactor this function",
            "Make this code cleaner",
            "Improve this implementation",
            "Simplify this logic",
        ]
        
        for query in queries:
            intent = detector._detect_intent_keywords(query)
            assert intent.intent_type == IntentType.REFACTOR
    
    def test_detect_optimize_intent(self):
        """Test detecting OPTIMIZE intent."""
        detector = AgentIntentDetector()
        
        queries = [
            "Optimize performance",
            "Make this faster",
            "Improve efficiency",
            "This is too slow",
        ]
        
        for query in queries:
            intent = detector._detect_intent_keywords(query)
            assert intent.intent_type == IntentType.OPTIMIZE
    
    def test_detect_diagnose_intent(self):
        """Test detecting DIAGNOSE intent."""
        detector = AgentIntentDetector()
        
        queries = [
            "Debug this error",
            "This is crashing",
            "Fix the bug",
            "What's wrong here?",
        ]
        
        for query in queries:
            intent = detector._detect_intent_keywords(query)
            assert intent.intent_type == IntentType.DIAGNOSE
    
    def test_detect_review_intent(self):
        """Test detecting REVIEW intent."""
        detector = AgentIntentDetector()
        
        queries = [
            "Review this code",
            "Check for bugs",
            "Audit this module",
            "Verify this works",
        ]
        
        for query in queries:
            intent = detector._detect_intent_keywords(query)
            assert intent.intent_type == IntentType.REVIEW
    
    def test_unknown_query_fallback(self):
        """Test unknown queries fall back to SUGGEST."""
        detector = AgentIntentDetector()
        
        intent = detector._detect_intent_keywords("xyzabc randomtext")
        assert intent.intent_type == IntentType.SUGGEST
        assert intent.confidence == 0.5
    
    def test_confidence_scores(self):
        """Test confidence scores for keyword matching."""
        detector = AgentIntentDetector()
        
        # Single keyword match should be lower confidence
        single = detector._detect_intent_keywords("explain")
        
        # Multiple keyword matches should be higher confidence
        multiple = detector._detect_intent_keywords("explain and tell me about this code")
        
        # Both should be confident, but multiple should be more so
        assert single.confidence < multiple.confidence


class TestAgentIntentDetectorLLM:
    """Test LLM-based intent detection."""
    
    @pytest.mark.asyncio
    async def test_detect_intent_with_llm(self):
        """Test LLM-based intent detection."""
        # Create mock provider chain
        mock_provider = AsyncMock()
        
        # Mock LLM response
        llm_response = json.dumps({
            "intent_type": "explain",
            "confidence": 0.95,
            "reasoning": "User asked to explain the function",
        })
        
        mock_provider.achat.return_value = ChatResponse(
            message=Message(role=Role.ASSISTANT, content=llm_response),
            provider="openai",
            model="gpt-4",
        )
        
        detector = AgentIntentDetector(provider_chain=mock_provider)
        
        intent = await detector.detect_intent("Explain this function")
        
        assert intent.intent_type == IntentType.EXPLAIN
        assert intent.confidence == 0.95
        assert intent.reasoning == "User asked to explain the function"
        assert mock_provider.achat.called
    
    @pytest.mark.asyncio
    async def test_detect_intent_llm_fallback(self):
        """Test fallback to keywords when LLM fails."""
        mock_provider = AsyncMock()
        mock_provider.achat.side_effect = Exception("LLM timeout")
        
        detector = AgentIntentDetector(provider_chain=mock_provider)
        
        # Should not raise, should fallback to keywords
        intent = await detector.detect_intent("Explain this function")
        
        assert intent.intent_type == IntentType.EXPLAIN
        assert intent.confidence < 1.0  # Keyword confidence
    
    @pytest.mark.asyncio
    async def test_detect_intent_no_provider(self):
        """Test detection without provider chain uses keywords."""
        detector = AgentIntentDetector(provider_chain=None)
        
        intent = await detector.detect_intent("Explain this function")
        
        assert intent.intent_type == IntentType.EXPLAIN
        assert "explain" in intent.reasoning
    
    def test_parse_llm_response_valid_json(self):
        """Test parsing valid LLM JSON response."""
        detector = AgentIntentDetector()
        
        response = json.dumps({
            "intent_type": "refactor",
            "confidence": 0.88,
            "reasoning": "Code quality improvement requested",
        })
        
        intent = detector._parse_llm_response(response, "test query")
        
        assert intent.intent_type == IntentType.REFACTOR
        assert intent.confidence == 0.88
    
    def test_parse_llm_response_json_with_extra_text(self):
        """Test parsing LLM response with extra text around JSON."""
        detector = AgentIntentDetector()
        
        response = """
        The user seems to want to improve the code.
        
        {
            "intent_type": "optimize",
            "confidence": 0.92,
            "reasoning": "Performance improvement requested"
        }
        
        This makes sense because they mentioned speed.
        """
        
        intent = detector._parse_llm_response(response, "test query")
        
        assert intent.intent_type == IntentType.OPTIMIZE
        assert intent.confidence == 0.92
    
    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON falls back to keywords."""
        detector = AgentIntentDetector()
        
        response = "This is not JSON at all"
        intent = detector._parse_llm_response(response, "explain this")
        
        # Should fallback to keywords
        assert intent.intent_type == IntentType.EXPLAIN
    
    def test_parse_llm_response_unknown_intent(self):
        """Test parsing response with unknown intent type."""
        detector = AgentIntentDetector()
        
        response = json.dumps({
            "intent_type": "unknown_intent",
            "confidence": 0.5,
            "reasoning": "Unknown",
        })
        
        intent = detector._parse_llm_response(response, "test query")
        
        # Should use SUGGEST as default
        assert intent.intent_type == IntentType.SUGGEST
    
    def test_parse_llm_confidence_bounds(self):
        """Test confidence is bounded to [0.0, 1.0]."""
        detector = AgentIntentDetector()
        
        # Test over 1.0
        response_high = json.dumps({
            "intent_type": "explain",
            "confidence": 2.5,
            "reasoning": "test",
        })
        intent_high = detector._parse_llm_response(response_high, "test")
        assert intent_high.confidence == 1.0
        
        # Test under 0.0
        response_low = json.dumps({
            "intent_type": "explain",
            "confidence": -0.5,
            "reasoning": "test",
        })
        intent_low = detector._parse_llm_response(response_low, "test")
        assert intent_low.confidence == 0.0


class TestAgentIntentDetectorCaching:
    """Test query caching."""
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache returns same result for same query."""
        detector = AgentIntentDetector()
        
        query = "Explain this function"
        intent1 = await detector.detect_intent(query)
        intent2 = await detector.detect_intent(query)
        
        # Should be exact same object from cache
        assert intent1 is intent2
    
    @pytest.mark.asyncio
    async def test_cache_different_queries(self):
        """Test different queries are not cached together."""
        detector = AgentIntentDetector()
        
        intent1 = await detector.detect_intent("Explain this")
        intent2 = await detector.detect_intent("Refactor that")
        
        # Should be different
        assert intent1.intent_type != intent2.intent_type
    
    @pytest.mark.asyncio
    async def test_cache_with_file_context(self):
        """Test caching with file context."""
        detector = AgentIntentDetector()
        
        query = "Explain this"
        context1 = {"file": "module.py"}
        context2 = {"file": "other.py"}
        
        intent1 = await detector.detect_intent(query, file_context=context1)
        intent2 = await detector.detect_intent(query, file_context=context2)
        intent3 = await detector.detect_intent(query, file_context=context1)
        
        # Same query + context should be cached
        assert intent1 is intent3
        
        # Different context is different cache entry
        # (May or may not be same intent, just different cache keys)
        assert intent2 is not intent1
    
    def test_cache_clear(self):
        """Test clearing cache."""
        detector = AgentIntentDetector()
        
        # Add to cache
        detector._query_cache["test"] = MagicMock()
        assert len(detector._query_cache) == 1
        
        # Clear
        detector.clear_cache()
        assert len(detector._query_cache) == 0
    
    def test_cache_stats(self):
        """Test getting cache statistics."""
        detector = AgentIntentDetector()
        
        intent = AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.9,
            reasoning="test",
        )
        detector._cache_intent("key1", intent)
        
        stats = detector.get_cache_stats()
        assert stats["cache_size"] == 1
        assert stats["max_cache_size"] == 256
    
    def test_cache_eviction(self):
        """Test LRU cache eviction when full."""
        detector = AgentIntentDetector()
        detector._max_cache_size = 3  # Small cache for testing
        
        intent1 = AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.9,
            reasoning="test1",
        )
        intent2 = AgentIntent(
            intent_type=IntentType.REFACTOR,
            agents_to_run=["refactor"],
            confidence=0.8,
            reasoning="test2",
        )
        intent3 = AgentIntent(
            intent_type=IntentType.OPTIMIZE,
            agents_to_run=["optimize"],
            confidence=0.7,
            reasoning="test3",
        )
        intent4 = AgentIntent(
            intent_type=IntentType.DIAGNOSE,
            agents_to_run=["diagnose"],
            confidence=0.6,
            reasoning="test4",
        )
        
        # Fill cache
        detector._cache_intent("key1", intent1)
        detector._cache_intent("key2", intent2)
        detector._cache_intent("key3", intent3)
        assert len(detector._query_cache) == 3
        
        # Add 4th item, should evict oldest
        detector._cache_intent("key4", intent4)
        assert len(detector._query_cache) == 3
        assert "key1" not in detector._query_cache  # Oldest evicted
        assert "key4" in detector._query_cache


class TestAgentIntentDetectorPrompts:
    """Test prompt generation."""
    
    def test_system_prompt_contains_intent_types(self):
        """Test system prompt includes all intent types."""
        detector = AgentIntentDetector()
        prompt = detector._build_system_prompt()
        
        for intent_type in IntentType:
            assert intent_type.value in prompt
    
    def test_system_prompt_contains_guidelines(self):
        """Test system prompt includes intent guidelines."""
        detector = AgentIntentDetector()
        prompt = detector._build_system_prompt()
        
        assert "EXPLAIN" in prompt
        assert "REFACTOR" in prompt
        assert "OPTIMIZE" in prompt
    
    def test_user_prompt_includes_query(self):
        """Test user prompt includes the query."""
        detector = AgentIntentDetector()
        query = "Test query"
        
        prompt = detector._build_user_prompt(query)
        assert query in prompt
    
    def test_user_prompt_includes_context(self):
        """Test user prompt includes file context when provided."""
        detector = AgentIntentDetector()
        query = "Test query"
        context = {
            "file": "module.py",
            "language": "python",
            "summary": "A test module",
        }
        
        prompt = detector._build_user_prompt(query, context)
        assert "module.py" in prompt
        assert "python" in prompt
        assert "A test module" in prompt


class TestAgentIntentDetectorIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_keyword_detection(self):
        """Test complete end-to-end keyword detection flow."""
        detector = AgentIntentDetector()
        
        intent = await detector.detect_intent(
            "Explain this function",
            file_context={"file": "utils.py"},
        )
        
        assert intent.intent_type == IntentType.EXPLAIN
        assert len(intent.agents_to_run) > 0
        assert 0.0 <= intent.confidence <= 1.0
        assert len(intent.reasoning) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_sequential_detections(self):
        """Test multiple intent detections in sequence."""
        detector = AgentIntentDetector()
        
        queries = [
            ("Explain the algorithm", IntentType.EXPLAIN),
            ("Refactor this function", IntentType.REFACTOR),
            ("Optimize performance", IntentType.OPTIMIZE),
            ("Debug this error", IntentType.DIAGNOSE),
        ]
        
        for query, expected_intent in queries:
            intent = await detector.detect_intent(query)
            assert intent.intent_type == expected_intent
    
    def test_detector_singleton_pattern(self):
        """Test module-level singleton getter."""
        from kicli_code_assist.agent.intent_detector import get_intent_detector
        
        detector1 = get_intent_detector()
        detector2 = get_intent_detector()
        
        # Should be same instance due to lru_cache
        assert detector1 is detector2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

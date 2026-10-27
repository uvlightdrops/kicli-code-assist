"""Phase 2D: Singleton instances for Agent components.

This module manages long-lived instances of Phase 2 components:
- AgentIntentDetector (Phase 2A): Intent classification
- AgentExecutor (Phase 2B): Agent execution
- ResultAggregator (Phase 2C): Result aggregation
- AnswerGenerator (Phase 2E): Conversational answer generation
"""

import logging
from pathlib import Path
from typing import Optional

from kicli_code_assist.agent.intent_detector import AgentIntentDetector
from kicli_code_assist.agent.executor import AgentExecutor
from kicli_code_assist.agent.aggregator import ResultAggregator
from kicli_code_assist.agent.answer_generator import AnswerGenerator
from ki_core.adapters import ProviderChain


# Module-level singletons
_intent_detector: Optional[AgentIntentDetector] = None
_executor: Optional[AgentExecutor] = None
_aggregator: Optional[ResultAggregator] = None
_answer_generator: Optional[AnswerGenerator] = None

_logger = logging.getLogger("kicli-web")


def get_intent_detector(project_root: Optional[Path] = None) -> AgentIntentDetector:
    """Get or create singleton AgentIntentDetector instance.
    
    Args:
        project_root: Optional project root (unused, kept for API compatibility)
        
    Returns:
        Singleton AgentIntentDetector instance
    """
    global _intent_detector
    if _intent_detector is None:
        _intent_detector = AgentIntentDetector()
        _logger.info("Initialized AgentIntentDetector (Phase 2A)")
    return _intent_detector


def get_executor(project_root: Optional[Path] = None) -> AgentExecutor:
    """Get or create singleton AgentExecutor instance.
    
    Args:
        project_root: Optional project root (defaults to cwd if None)
        
    Returns:
        Singleton AgentExecutor instance
    """
    global _executor
    if _executor is None:
        if project_root is None:
            project_root = Path.cwd()
        _executor = AgentExecutor(
            project_root=project_root,
            intent_detector=get_intent_detector(),
            enable_cache=True
        )
        _logger.info("Initialized AgentExecutor (Phase 2B)")
    return _executor


def get_aggregator(provider_chain: Optional[ProviderChain] = None) -> ResultAggregator:
    """Get or create singleton ResultAggregator instance.
    
    Args:
        provider_chain: Optional custom provider chain (defaults to openai)
        
    Returns:
        Singleton ResultAggregator instance
    """
    global _aggregator
    if _aggregator is None:
        _aggregator = ResultAggregator(
            provider="openai",
            provider_chain=provider_chain,
            enable_llm=True
        )
        _logger.info("Initialized ResultAggregator (Phase 2C)")
    return _aggregator


def get_answer_generator(provider_chain: Optional[ProviderChain] = None) -> AnswerGenerator:
    """Get or create singleton AnswerGenerator instance.
    
    Args:
        provider_chain: Optional custom provider chain
        
    Returns:
        Singleton AnswerGenerator instance
    """
    global _answer_generator
    if _answer_generator is None:
        _answer_generator = AnswerGenerator(provider_chain=provider_chain)
        _logger.info("Initialized AnswerGenerator (Phase 2E)")
    return _answer_generator


def reset_all():
    """Reset all singleton instances (for testing)."""
    global _intent_detector, _executor, _aggregator, _answer_generator
    _intent_detector = None
    _executor = None
    _aggregator = None
    _answer_generator = None
    _logger.info("Reset all Phase 2D singleton instances")

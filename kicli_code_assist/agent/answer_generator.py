"""LLM-based answer generator for conversational responses (Phase 2E).

This module generates natural language answers to user queries based on
analysis results, creating true conversational responses instead of just
technical summaries.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from ki_core.core.models import ChatRequest, Message, Role

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Context from various analyzers to inform the answer."""
    query: str
    file_path: str
    structure: Optional[Dict] = None
    metrics: Optional[Dict] = None
    dependencies: Optional[Dict] = None
    refactor_suggestions: Optional[Dict] = None


class AnswerGenerator:
    """Generate conversational answers based on analysis results.
    
    Uses LLM to synthesize technical analysis into natural language
    responses that directly answer user questions.
    """
    
    def __init__(self, provider_chain=None):
        """Initialize the answer generator.
        
        Args:
            provider_chain: Optional ProviderChain for LLM calls
        """
        self.provider_chain = provider_chain
    
    async def generate_answer(
        self,
        query: str,
        context: AnalysisContext,
    ) -> str:
        """Generate a conversational answer to the user query.
        
        Args:
            query: Original user query
            context: AnalysisContext with analysis results
            
        Returns:
            Natural language answer in the user's language (German/English)
        """
        if not self.provider_chain:
            return self._fallback_answer(query, context)
        
        try:
            prompt = self._build_answer_prompt(query, context)
            request = ChatRequest(
                messages=[
                    Message(
                        role=Role.SYSTEM,
                        content=self._build_system_prompt(),
                    ),
                    Message(role=Role.USER, content=prompt),
                ],
                temperature=0.7,  # More creative than classification
                max_tokens=500,
            )
            
            response = await self.provider_chain.achat(request)
            answer = response.message.content
            
            logger.debug(f"Generated answer ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.warning(f"LLM answer generation failed: {e}, using fallback")
            return self._fallback_answer(query, context)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for answer generation."""
        return """You are a helpful code analysis assistant that explains code to developers.
Your answers should be:
- Direct and conversational (not just listing facts)
- In the same language as the query (German or English)
- Focused on answering the specific question asked
- Concise but informative (2-4 sentences typically)
- Technical but accessible

If the query is in German, respond in German.
If the query is in English, respond in English."""
    
    def _build_answer_prompt(
        self,
        query: str,
        context: AnalysisContext,
    ) -> str:
        """Build the prompt for generating an answer.
        
        Args:
            query: Original user query
            context: Analysis results
            
        Returns:
            Formatted prompt for the LLM
        """
        file_name = context.file_path.split('/')[-1]
        
        prompt = f"""User question: {query}

File being analyzed: {file_name}

Analysis results:
"""
        
        if context.structure:
            s = context.structure
            classes_count = len(s.get('classes', {}))
            functions_count = len(s.get('functions', {}))
            prompt += f"\n- Structure: {functions_count} functions, {classes_count} classes"
            if functions_count > 0:
                funcs = list(s.get('functions', {}).keys())[:3]
                prompt += f" (main: {', '.join(funcs)})"
        
        if context.metrics:
            m = context.metrics
            if 'maintainability_index' in m:
                prompt += f"\n- Maintainability: {m['maintainability_index']:.0f}/100"
            if 'average_complexity' in m:
                prompt += f"\n- Complexity: {m['average_complexity']:.1f} (average)"
            if 'issues' in m:
                prompt += f"\n- Issues found: {len(m['issues'])}"
        
        if context.dependencies:
            d = context.dependencies
            prompt += f"\n- Dependencies: {len(d.get('externals', {}))} external, {len(d.get('internals', {}))} internal"
            if d.get('circular_dependencies'):
                prompt += f" ({len(d['circular_dependencies'])} circular)"
        
        if context.refactor_suggestions:
            r = context.refactor_suggestions
            if r.get('recommendations'):
                prompt += f"\n- Refactoring suggestions: {len(r['recommendations'])} recommendations"
        
        prompt += "\n\nBased on these results, answer the user's question directly."
        return prompt
    
    def _fallback_answer(
        self,
        query: str,
        context: AnalysisContext,
    ) -> str:
        """Fallback answer generation without LLM.
        
        Args:
            query: Original user query
            context: Analysis results
            
        Returns:
            Simple templated answer
        """
        file_name = context.file_path.split('/')[-1]
        
        # Detect query language (simple heuristic)
        is_german = any(word in query.lower() for word in ['erkläre', 'zeige', 'optimiere', 'überprüfe', 'diese'])
        
        if context.structure:
            funcs = len(context.structure.get('functions', {}))
            classes = len(context.structure.get('classes', {}))
            
            if is_german:
                base = f"Die Datei {file_name} enthält {funcs} Funktionen"
                if classes > 0:
                    base += f" und {classes} Klassen"
                base += "."
            else:
                base = f"The file {file_name} contains {funcs} functions"
                if classes > 0:
                    base += f" and {classes} classes"
                base += "."
            
            if context.metrics and 'maintainability_index' in context.metrics:
                mi = context.metrics['maintainability_index']
                if is_german:
                    base += f" Die Wartbarkeit liegt bei {mi:.0f}/100."
                else:
                    base += f" Maintainability: {mi:.0f}/100."
            
            return base
        
        if is_german:
            return f"Die Analyse der Datei {file_name} ist abgeschlossen. Siehe die Registerkarten für Details."
        else:
            return f"Analysis of {file_name} complete. See the tabs for details."

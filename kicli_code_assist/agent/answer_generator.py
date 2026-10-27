"""LLM-based answer generator for conversational responses (Phase 2E).

This module generates detailed, conversational natural language answers to user 
queries based on analysis results, creating true conversational responses instead 
of just technical summaries.
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
    
    Uses LLM to synthesize technical analysis into detailed natural language
    responses that directly answer user questions in 3-5+ sentences.
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
        """Generate a detailed conversational answer to the user query.
        
        Args:
            query: Original user query
            context: AnalysisContext with analysis results
            
        Returns:
            Detailed natural language answer (3-5+ sentences) in user's language
        """
        if not self.provider_chain:
            return self._fallback_answer_detailed(query, context)
        
        try:
            prompt = self._build_answer_prompt_detailed(query, context)
            request = ChatRequest(
                messages=[
                    Message(
                        role=Role.SYSTEM,
                        content=self._build_system_prompt_detailed(),
                    ),
                    Message(role=Role.USER, content=prompt),
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            
            response = await self.provider_chain.achat(request)
            answer = response.message.content
            
            logger.debug(f"Generated detailed answer ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.warning(f"LLM answer generation failed: {e}, using fallback")
            return self._fallback_answer_detailed(query, context)
    
    def _build_system_prompt_detailed(self) -> str:
        """Build system prompt for detailed answer generation."""
        return """You are an expert code analysis assistant that provides detailed, thorough explanations of code to developers.

Your response guidelines:
- Write 3-5+ detailed sentences minimum (be comprehensive)
- Use the same language as the user's query (German or English)
- Focus directly on answering the specific question
- Be technical but accessible
- Include specific details about structure, purpose, quality, complexity
- For "Explain": describe what the code does, its purpose, key functions/classes
- For "Optimize": focus on performance issues and improvement opportunities
- For "Review": highlight quality issues and best practice violations
- Provide actionable insights and recommendations

Response style:
- Start with a clear statement of what the code does
- Explain the structure and key components
- Discuss quality and complexity metrics
- Mention notable characteristics or issues
- Suggest improvements if relevant
- Be thorough, specific, and helpful

If German: Antworte auf Deutsch
If English: Respond in English"""

    def _build_answer_prompt_detailed(self, query: str, context: AnalysisContext) -> str:
        """Build a detailed prompt for comprehensive answers."""
        file_name = context.file_path.split('/')[-1]
        prompt = f"""User question: {query}
File: {file_name}

Analysis data to synthesize:
"""
        
        if context.structure:
            s = context.structure
            classes_count = len(s.get('classes', {}))
            functions_count = len(s.get('functions', {}))
            imports_count = len(s.get('imports', []))
            
            prompt += f"\nSTRUCTURE:\n"
            prompt += f"- {functions_count} functions, {classes_count} classes, {imports_count} imports\n"
            
            if classes_count > 0:
                classes = list(s.get('classes', {}).keys())[:5]
                prompt += f"- Classes: {', '.join(classes)}\n"
            
            if functions_count > 0:
                funcs = list(s.get('functions', {}).keys())[:10]
                prompt += f"- Functions: {', '.join(funcs)}\n"
        
        if context.metrics:
            m = context.metrics
            prompt += f"\nQUALITY METRICS:\n"
            
            if 'maintainability_index' in m:
                mi = m['maintainability_index']
                quality = "high (>80)" if mi > 80 else "medium (50-80)" if mi > 50 else "low (<50)"
                prompt += f"- Maintainability Index: {mi:.0f}/100 ({quality})\n"
            
            if 'average_complexity' in m:
                ac = m['average_complexity']
                level = "low" if ac < 3 else "medium" if ac < 7 else "high"
                prompt += f"- Avg Cyclomatic Complexity: {ac:.1f} ({level})\n"
            
            if 'lines_of_code' in m:
                prompt += f"- Lines of Code: {m['lines_of_code']}\n"
            
            if 'issues' in m and m['issues']:
                prompt += f"- Issues/Warnings: {len(m['issues'])} found\n"
                for issue in m['issues'][:3]:
                    prompt += f"  • {issue}\n"
        
        if context.dependencies:
            d = context.dependencies
            prompt += f"\nDEPENDENCIES:\n"
            prompt += f"- {len(d.get('externals', {}))} external, {len(d.get('internals', {}))} internal\n"
            
            if d.get('circular_dependencies'):
                prompt += f"- ⚠️ {len(d['circular_dependencies'])} circular dependencies\n"
        
        if context.refactor_suggestions:
            r = context.refactor_suggestions
            if r.get('recommendations'):
                prompt += f"\nREFACTORING OPPORTUNITIES:\n"
                for rec in r['recommendations'][:5]:
                    prompt += f"- {rec}\n"
        
        prompt += f"""
Now write a detailed, conversational answer to the user's question.
Be thorough (3-5+ sentences), specific (use numbers/names from the analysis), 
and helpful (provide insights and recommendations).
Address the specific question they asked."""
        
        return prompt
    
    def _fallback_answer_detailed(self, query: str, context: AnalysisContext) -> str:
        """Generate detailed fallback answer without LLM."""
        file_name = context.file_path.split('/')[-1]
        is_german = any(w in query.lower() for w in ['erkläre', 'zeige', 'optimiere', 'überprüfe', 'analyse'])
        
        parts = []
        
        # Opening
        if is_german:
            parts.append(f"Die Datei {file_name} ist eine Python-Komponente mit folgender Struktur:")
        else:
            parts.append(f"The file {file_name} is a Python component with the following structure:")
        
        # Structure details
        if context.structure:
            s = context.structure
            funcs = len(s.get('functions', {}))
            classes = len(s.get('classes', {}))
            
            if is_german:
                parts.append(f"Sie enthält {funcs} Funktionen{'und ' + str(classes) + ' Klassen' if classes > 0 else ''}.")
                if funcs > 0:
                    func_names = list(s.get('functions', {}).keys())[:3]
                    parts.append(f"Die Hauptfunktionen sind: {', '.join(func_names)}.")
            else:
                parts.append(f"It contains {funcs} functions{' and ' + str(classes) + ' classes' if classes > 0 else ''}.")
                if funcs > 0:
                    func_names = list(s.get('functions', {}).keys())[:3]
                    parts.append(f"Key functions include: {', '.join(func_names)}.")
        
        # Quality metrics
        if context.metrics:
            m = context.metrics
            if 'maintainability_index' in m:
                mi = m['maintainability_index']
                if is_german:
                    quality_de = "gut" if mi > 80 else "befriedigend" if mi > 50 else "verbesserungsbedürftig"
                    parts.append(f"Die Wartbarkeit liegt bei {mi:.0f}/100 ({quality_de}).")
                else:
                    quality_en = "good" if mi > 80 else "fair" if mi > 50 else "needs improvement"
                    parts.append(f"Maintainability score: {mi:.0f}/100 ({quality_en}).")
        
        # Issues
        if context.metrics and context.metrics.get('issues'):
            if is_german:
                parts.append(f"Es wurden {len(context.metrics['issues'])} Code-Probleme identifiziert, die beachtet werden sollten.")
            else:
                parts.append(f"There are {len(context.metrics['issues'])} code issues identified that should be addressed.")
        
        # Suggestions
        if context.refactor_suggestions and context.refactor_suggestions.get('recommendations'):
            if is_german:
                parts.append(f"Für Verbesserungen siehe die Registerkarten 'Structure', 'Metrics' und 'Refactor' für detaillierte Empfehlungen.")
            else:
                parts.append(f"For improvement details, see the 'Structure', 'Metrics', and 'Refactor' tabs for specific recommendations.")
        
        return " ".join(parts) if parts else (
            "Die Analyse ist abgeschlossen. Siehe die Registerkarten für detaillierte Ergebnisse."
            if is_german
            else "Analysis complete. See the tabs for detailed results."
        )

"""
Async Scorer for Langfuse

Provides non-blocking, rule-based quality scoring for agent outputs.
Works alongside Langfuse UI evaluators for comprehensive LLM-as-judge evaluation.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

# Langfuse client for scoring
try:
    from langfuse.decorators import langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class AsyncScorer:
    """
    Async scorer for agent outputs using simple rule-based checks.
    
    Provides fast, non-blocking scoring that complements deep LLM-based
    evaluation configured in Langfuse UI.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("catalyze.async_scorer")
    
    @staticmethod
    async def score_response(
        query: str,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None
    ) -> None:
        """
        Score agent response with rule-based metrics (non-blocking)
        
        Args:
            query: User's original query
            output: Agent's response
            context: Additional context dictionary
            agent_name: Name of the agent that generated the response
        """
        if not LANGFUSE_AVAILABLE:
            return
        
        try:
            # Calculate simple rule-based scores
            scores = AsyncScorer._calculate_scores(query, output, context, agent_name)
            
            # Submit scores to Langfuse asynchronously
            for name, value in scores.items():
                try:
                    langfuse_context.score_current_trace(
                        name=name,
                        value=value
                    )
                except Exception as e:
                    # Silently fail - scoring should never block main flow
                    pass
                    
        except Exception as e:
            # Silently fail - scoring should never interrupt main flow
            pass
    
    @staticmethod
    def _calculate_scores(
        query: str,
        output: str,
        context: Optional[Dict[str, Any]],
        agent_name: Optional[str]
    ) -> Dict[str, float]:
        """
        Calculate rule-based scores for the response
        
        Returns:
            Dictionary of score names to values (0.0-1.0)
        """
        scores = {}
        
        # 1. Response length score (0.0 = too short, 1.0 = good length)
        output_length = len(output)
        if output_length < 50:
            scores["response_length_quality"] = 0.0
        elif output_length < 200:
            scores["response_length_quality"] = 0.5
        elif output_length < 2000:
            scores["response_length_quality"] = 1.0
        else:
            scores["response_length_quality"] = 0.8  # Very long responses penalized slightly
        
        # 2. Safety information presence (binary)
        safety_keywords = ["safety", "hazard", "danger", "warning", "caution", "ppe", "protective"]
        has_safety = any(kw in output.lower() for kw in safety_keywords)
        scores["has_safety_info"] = 1.0 if has_safety else 0.0
        
        # 3. Source/citation presence (binary)
        source_keywords = ["chembl", "pubchem", "source", "according to", "reference", "documentation"]
        has_sources = any(kw in output.lower() for kw in source_keywords)
        scores["has_citations"] = 1.0 if has_sources else 0.0
        
        # 4. Code quality (for code generation responses)
        if agent_name and "automate" in agent_name.lower():
            has_imports = "import" in output or "from" in output
            has_function = "def " in output
            has_comments = "#" in output
            
            code_quality = 0.0
            if has_imports:
                code_quality += 0.33
            if has_function or "class " in output:
                code_quality += 0.33
            if has_comments:
                code_quality += 0.34
            
            scores["code_quality"] = code_quality
        
        # 5. Relevance heuristic (keyword matching)
        query_words = set(query.lower().split())
        output_words = set(output.lower().split())
        
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        query_words = query_words - stop_words
        output_words = output_words - stop_words
        
        if len(query_words) > 0:
            overlap = len(query_words.intersection(output_words))
            relevance_score = min(overlap / len(query_words), 1.0)
            scores["keyword_relevance"] = relevance_score
        
        # 6. Completeness indicators
        completeness_keywords = ["steps", "first", "then", "next", "finally", "ml", "µl", "temperature"]
        completeness_count = sum(1 for kw in completeness_keywords if kw in output.lower())
        scores["completeness_indicators"] = min(completeness_count / 5.0, 1.0)
        
        # 7. Error/failure indicators (inverted - lower is better)
        error_keywords = ["error", "failed", "cannot", "unable", "not available", "don't know"]
        has_errors = any(kw in output.lower() for kw in error_keywords)
        scores["error_free"] = 0.0 if has_errors else 1.0
        
        return scores
    
    @staticmethod
    def trigger_async_scoring(
        query: str,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None
    ) -> None:
        """
        Trigger scoring in the background (fire-and-forget)
        
        This is the main entry point for non-blocking scoring.
        Call this after generating a response to score it asynchronously.
        """
        if not LANGFUSE_AVAILABLE:
            return
        
        # Create background task (don't await it)
        try:
            asyncio.create_task(
                AsyncScorer.score_response(query, output, context, agent_name)
            )
        except RuntimeError:
            # No event loop running - skip scoring
            pass


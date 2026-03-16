"""Web Search Agent: Smart fetching with heuristics and source counting"""

import re
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class WebSearchIntent(str, Enum):
    """Classified intent of a query"""
    DEFINITION = "definition"      # "What is X?", "Explain X"
    HOWTO = "howto"                # "How to X?", "Steps to X"
    FACTUAL = "factual"            # "When was X?", "Who is X?"
    OPINION = "opinion"            # "Best X?", "Should I X?"
    RECENT = "recent"              # "Latest X?", "2024 X?"
    UNKNOWN = "unknown"            # Uncertain


class WebSearchHeuristic:
    """Analyzes queries to determine if web search is necessary"""

    # Query patterns for each intent
    DEFINITION_PATTERNS = [
        r"\b(what|define|explain|describe|clarify|meaning of)\b",
        r"\b(is|are|definition|definition of)\b",
        r"\b(concept of|term|terminology)\b"
    ]

    HOWTO_PATTERNS = [
        r"\b(how to|how can|steps to|way to|process)\b",
        r"\b(guide|tutorial|teach me|learn to)\b",
        r"\b(install|setup|configure|run)\b"
    ]

    FACTUAL_PATTERNS = [
        r"\b(when|where|who|which|what happened)\b",
        r"\b(history|founded|created|birth)\b",
        r"\b(date|year|time|period)\b"
    ]

    OPINION_PATTERNS = [
        r"\b(best|worst|better|worse|should|recommend|prefer)\b",
        r"\b(pros and cons|advantages|disadvantages|benefits)\b",
        r"\b(opinion|think|believe|best practice)\b"
    ]

    RECENT_PATTERNS = [
        r"\b(latest|recent|2024|2023|new|today|this year)\b",
        r"\b(current|ongoing|happening now|now)\b",
        r"\b(future|upcoming|announced)\b"
    ]

    @staticmethod
    def classify_intent(query: str) -> WebSearchIntent:
        """Classify query intent"""
        query_lower = query.lower()
        
        # Check for recent intent first (highest priority)
        for pattern in WebSearchHeuristic.RECENT_PATTERNS:
            if re.search(pattern, query_lower):
                return WebSearchIntent.RECENT

        # Check definition
        for pattern in WebSearchHeuristic.DEFINITION_PATTERNS:
            if re.search(pattern, query_lower):
                return WebSearchIntent.DEFINITION

        # Check how-to
        for pattern in WebSearchHeuristic.HOWTO_PATTERNS:
            if re.search(pattern, query_lower):
                return WebSearchIntent.HOWTO

        # Check factual
        for pattern in WebSearchHeuristic.FACTUAL_PATTERNS:
            if re.search(pattern, query_lower):
                return WebSearchIntent.FACTUAL

        # Check opinion
        for pattern in WebSearchHeuristic.OPINION_PATTERNS:
            if re.search(pattern, query_lower):
                return WebSearchIntent.OPINION

        return WebSearchIntent.UNKNOWN

    @staticmethod
    def should_search_web(query: str) -> bool:
        """
        Heuristic: determine if web search is necessary
        
        Skip web search for:
        - Definition/explanation queries (can be answered from training data)
        - How-to queries if general knowledge (can be answered from training data)
        
        Need web search for:
        - Recent/news queries (time-sensitive data)
        - Opinion queries (current consensus needed)
        - Factual queries about recent events
        """
        intent = WebSearchHeuristic.classify_intent(query)

        # Skip web for these intents
        if intent == WebSearchIntent.DEFINITION:
            logger.info(f"Query classified as DEFINITION; skipping web search")
            return False

        if intent == WebSearchIntent.HOWTO:
            # Only skip if no specific tool/product mentioned
            if not re.search(r"\b(install|setup|configure|how to [a-z]+)\b", query.lower()):
                logger.info(f"Query classified as general HOWTO; skipping web search")
                return False

        # For all other intents, search web
        logger.info(f"Query classified as {intent}; will search web")
        return True

    @staticmethod
    def recommended_source_count(intent: WebSearchIntent) -> int:
        """
        Recommend source count based on intent
        
        Definition: 2-3 sources
        How-to: 3-5 sources
        Factual: 5-8 sources
        Recent: 8-15 sources
        Opinion: 10-20 sources
        """
        recommendations = {
            WebSearchIntent.DEFINITION: 3,
            WebSearchIntent.HOWTO: 4,
            WebSearchIntent.FACTUAL: 6,
            WebSearchIntent.RECENT: 10,
            WebSearchIntent.OPINION: 12,
            WebSearchIntent.UNKNOWN: 5,
        }
        return recommendations.get(intent, 5)


class IWebFetcher(ABC):
    """Abstract interface for web fetchers"""

    @abstractmethod
    async def fetch(
        self,
        query: str,
        max_sources: int,
        timeout: float,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch sources from web"""
        pass


class WebFetcherAgent:
    """Orchestrates web fetching with smart heuristics"""

    def __init__(self, web_fetcher: IWebFetcher):
        """Args: web_fetcher (implementation of IWebFetcher)"""
        self.fetcher = web_fetcher

    async def smart_fetch(
        self,
        query: str,
        user_max_sources: Optional[int] = None,
        force_search: bool = False,
        request_timeout: float = 15.0
    ) -> tuple:
        """
        Smart decision: whether to search web and fetch sources
        
        Returns:
            (should_search, sources_list)
        """
        # Check if web search is necessary
        if not force_search and not WebSearchHeuristic.should_search_web(query):
            logger.info(f"Query doesn't require web search: {query[:50]}")
            return (False, [])

        # Determine target source count
        intent = WebSearchHeuristic.classify_intent(query)
        recommended = WebSearchHeuristic.recommended_source_count(intent)
        max_sources = user_max_sources or recommended

        logger.info(f"Fetching {max_sources} sources for query: {query[:50]}... (intent: {intent})")

        # Fetch sources
        try:
            sources = await self.fetcher.fetch(
                query=query,
                max_sources=max_sources,
                timeout=request_timeout
            )
            logger.info(f"Fetched {len(sources)} sources")
            return (True, sources)
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return (True, [])

    @staticmethod
    def validate_source_count(requested: int, cpu_budget: float) -> int:
        """Validate & adjust source count based on CPU budget"""
        # Map CPU budget to source cap
        if cpu_budget <= 50:
            max_allowed = 3
        elif cpu_budget <= 70:
            max_allowed = 5
        elif cpu_budget <= 90:
            max_allowed = 10
        else:
            max_allowed = 20

        adjusted = min(requested, max_allowed)
        if adjusted < requested:
            logger.warning(
                f"Source count adjusted {requested} → {adjusted} "
                f"due to CPU budget {cpu_budget}%"
            )
        return adjusted

"""Response Synthesis: Output format factory (Quick/Full/Paper)"""

import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum
import re

logger = logging.getLogger(__name__)


class OutputMode(str, Enum):
    """Output format modes"""
    QUICK = "quick"          # 1-2 sentences, minimal analysis
    FULL = "full"            # Detailed with all thinking visible
    PAPER = "paper"          # Academic format with abstract, sections, citations


class IResponseFormatter(ABC):
    """Abstract response formatter interface"""

    @abstractmethod
    def format(
        self,
        query: str,
        thinking: str,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """Format response according to mode"""
        pass


class QuickFormatter(IResponseFormatter):
    """Format: Quick (ultra-condensed, <2 sentences)"""

    def format(
        self,
        query: str,
        thinking: str,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """Extract 1-2 key sentences from response"""
        
        # Extract first substantive sentence(s)
        sentences = re.split(r"(?<=[.!?])\s+", response.strip())
        key_sentences = []
        char_count = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue
            
            key_sentences.append(sent)
            char_count += len(sent)
            
            if len(key_sentences) >= 2 or char_count > 300:
                break
        
        quick_response = " ".join(key_sentences)[:350]
        
        # Add minimal sources
        if sources:
            quick_response += f"\n\n**From**: {sources[0].get('title', 'Source')}"
        
        return quick_response


class FullFormatter(IResponseFormatter):
    """Format: Full (detailed with thinking, all sources)"""

    def format(
        self,
        query: str,
        thinking: str,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """Full response with thinking and all sources"""
        
        output = f"""
# Research: {query}

## Research Plan
```
{thinking}
```

## Analysis
{response}
"""
        
        if sources:
            output += "\n## Sources\n"
            for idx, source in enumerate(sources, 1):
                title = source.get('title', f'Source {idx}')
                url = source.get('url', '#')
                output += f"\n{idx}. [{title}]({url})"
                if source.get('excerpt'):
                    output += f"\n   > {source['excerpt'][:200]}..."
        
        return output


class PaperFormatter(IResponseFormatter):
    """Format: Paper (academic with abstract, methodology, conclusion)"""

    def format(
        self,
        query: str,
        thinking: str,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """Academic paper format"""
        
        # Extract abstract (first 200 chars)
        abstract_sentences = re.split(r"(?<=[.!?])\s+", response.strip())[:2]
        abstract = " ".join(abstract_sentences)[:200]
        
        # Build paper structure
        output = f"""
# {query}

## Abstract

{abstract}

## Introduction

This research explores the topic of **{query}**. The primary objective is to provide a comprehensive analysis based on current web research and domain knowledge.

## Research Methodology

**Approach**: Multi-source web research with content analysis and synthesis.

**Search Strategy**: Web search and knowledge base consultation.

**Sources Consulted**: {len(sources)} primary sources were analyzed during this research.

## Findings & Analysis

{response}

## Conclusion

Based on the research conducted, the topic of **{query}** has been thoroughly explored from multiple perspectives and sources.

## References

"""
        
        # Add references in academic format
        if sources:
            output += "\n"
            for idx, source in enumerate(sources, 1):
                title = source.get('title', f'Source {idx}')
                url = source.get('url', '')
                output += f"\n[{idx}] {title}. Available at: {url}"
        
        return output


class ResponseSynthesizer:
    """Factory for creating formatted responses"""

    _formatters = {
        OutputMode.QUICK: QuickFormatter(),
        OutputMode.FULL: FullFormatter(),
        OutputMode.PAPER: PaperFormatter(),
    }

    @classmethod
    def synthesize(
        cls,
        mode: OutputMode,
        query: str,
        thinking: str,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize response in requested format
        
        Args:
            mode: OutputMode enum
            query: Original research query
            thinking: AI's thinking/plan
            response: Generated response
            sources: List of web sources
        
        Returns:
            Formatted response string
        """
        formatter = cls._formatters.get(mode, cls._formatters[OutputMode.FULL])
        logger.info(f"Synthesizing response in {mode} mode")
        return formatter.format(query, thinking, response, sources)

    @classmethod
    def get_available_modes(cls) -> List[str]:
        """Get list of available output modes"""
        return [mode.value for mode in OutputMode]

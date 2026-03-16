"""Research Agent Core Module - Enterprise-grade OOP Architecture"""

from .config import ConfigManager, GPUDetector, CPUProfiler, OutputMode
from .orchestrator import ResearchOrchestrator
from .fetcher import WebFetcherAgent, WebSearchHeuristic
from .synthesizer import ResponseSynthesizer
from .persistence import SessionRepository, FileBackend
from .resources import ResourceManager, CPULimiter, GPUAllocator

__all__ = [
    'ConfigManager',
    'GPUDetector',
    'CPUProfiler',
    'OutputMode',
    'ResearchOrchestrator',
    'WebFetcherAgent',
    'WebSearchHeuristic',
    'ResponseSynthesizer',
    'SessionRepository',
    'FileBackend',
    'ResourceManager',
    'CPULimiter',
    'GPUAllocator',
]

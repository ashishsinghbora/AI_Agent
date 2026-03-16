"""Research Orchestrator: Main agent coordinating all research tasks"""

import logging
import asyncio
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates the complete research flow"""

    def __init__(
        self,
        config_manager,
        ollama_manager,
        web_fetcher_agent,
        response_synthesizer,
        vector_store,
        resource_manager,
        session_repository,
        file_backend
    ):
        """
        Initialize orchestrator with dependencies (Dependency Injection)
        
        Args:
            config_manager: ConfigManager instance
            ollama_manager: OllamaManager for model inference
            web_fetcher_agent: WebFetcherAgent for smart fetching
            response_synthesizer: ResponseSynthesizer for formatting
            vector_store: VectorStore for persistence
            resource_manager: ResourceManager for resource allocation
            session_repository: SessionRepository for DB persistence
            file_backend: FileBackend for JSON snapshots
        """
        self.config = config_manager
        self.ollama = ollama_manager
        self.fetcher_agent = web_fetcher_agent
        self.synthesizer = response_synthesizer
        self.vector_store = vector_store
        self.resource_manager = resource_manager
        self.session_repo = session_repository
        self.file_backend = file_backend

    async def research(
        self,
        query: str,
        output_mode: str = "quick",
        max_sources: int = 5,
        cpu_budget_percent: float = 80.0,
        use_thinking: bool = True,
        thinking_chars: int = 180,
        preferred_domains: Optional[List[str]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute complete research flow with streaming events
        
        Yields:
            JSON event strings (one per line, NDJSON format)
        """
        from .persistence import ResearchSession
        from .synthesizer import OutputMode, ResponseSynthesizer

        session_id = datetime.now().isoformat()
        chat_history = chat_history or []
        preferred_domains = preferred_domains or []

        # Create session object
        session = ResearchSession(
            session_id=session_id,
            query=query,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="in_progress",
            output_mode=output_mode,
            findings_count=0,
            sources=[],
            thinking="",
            response="",
            metadata={"cpu_budget": cpu_budget_percent}
        )

        # Save initial session to DB
        self.session_repo.create_session(session)

        try:
            # Phase 1: Emit status
            yield json.dumps({
                "type": "status",
                "message": f"Starting research for: {query[:50]}...",
                "progress": 5
            }) + "\n"

            # Phase 2: Thinking (if enabled)
            accumulated_thinking = ""
            if use_thinking:
                yield json.dumps({"type": "thinking_start", "timestamp": datetime.now().isoformat()}) + "\n"
                
                thinking_prompt = f"Create a very short research plan (max 2 bullets, 25 words).\n\nQuery: {query}"
                
                async for chunk in self.ollama.generate_streaming(
                    prompt=thinking_prompt,
                    model="gemma2:2b",  # Fast model for planning
                    temperature=0.2,
                    max_tokens=min(thinking_chars, 200)
                ):
                    accumulated_thinking += chunk
                    yield json.dumps({"type": "thinking", "content": chunk}) + "\n"
                
                session.thinking = accumulated_thinking
                yield json.dumps({"type": "thinking_end", "timestamp": datetime.now().isoformat()}) + "\n"

            # Phase 3: Smart web search
            yield json.dumps({
                "type": "status",
                "message": "Analyzing query and fetching sources...",
                "progress": 20
            }) + "\n"

            # Allocate resources
            resources = self.resource_manager.allocate_resources(
                max_sources=max_sources,
                cpu_budget_percent=cpu_budget_percent
            )

            # Smart fetch with heuristics
            did_search, sources = await self.fetcher_agent.smart_fetch(
                query=query,
                user_max_sources=max_sources,
                force_search=False,
                request_timeout=15.0
            )

            if did_search:
                yield json.dumps({
                    "type": "sources_found",
                    "sources": sources,
                    "count": len(sources),
                    "progress": 35
                }) + "\n"
                session.sources = sources
                session.findings_count = len(sources)

            # Phase 4: Generate response
            yield json.dumps({
                "type": "status",
                "message": "Generating response...",
                "progress": 60
            }) + "\n"

            # Build context from sources and vector store
            context_docs = await self.vector_store.search(query, top_k=3)
            context_str = "\n".join([
                f"- {doc.get('metadata', {}).get('title', 'Doc')}: {doc.get('content', '')[:200]}..."
                for doc in context_docs
            ])

            response_prompt = f"""
Based on this research about '{query}':

Context:
{context_str}

Provide a clear, structured answer with practical insights.
"""

            accumulated_response = ""
            yield json.dumps({"type": "response_start", "progress": 70}) + "\n"

            async for chunk in self.ollama.generate_streaming(
                prompt=response_prompt,
                model="gemma2:2b",
                temperature=0.5,
                max_tokens=1500
            ):
                accumulated_response += chunk
                yield json.dumps({"type": "response", "content": chunk}) + "\n"

            session.response = accumulated_response

            # Phase 5: Synthesize in requested format
            logger.info(f"Synthesizing in {output_mode} mode")
            try:
                output_mode_enum = OutputMode[output_mode.upper()]
            except (KeyError, AttributeError):
                output_mode_enum = OutputMode.QUICK

            synthesized_response = ResponseSynthesizer.synthesize(
                mode=output_mode_enum,
                query=query,
                thinking=accumulated_thinking,
                response=accumulated_response,
                sources=sources
            )

            session.response = synthesized_response

            # Phase 6: Persist and complete
            yield json.dumps({
                "type": "status",
                "message": "Saving research...",
                "progress": 90
            }) + "\n"

            # Save to DB and file
            session.status = "completed"
            session.updated_at = datetime.now().isoformat()
            self.session_repo.update_session(session)
            await self.file_backend.save_session_snapshot(session)

            # Store in vector store
            for source in sources:
                await self.vector_store.add_document(
                    content=source.get("content", source.get("snippet", "")),
                    metadata={
                        "url": source.get("url"),
                        "title": source.get("title"),
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # Final completion event
            yield json.dumps({
                "type": "research_complete",
                "message": "Research complete!",
                "session_id": session_id,
                "output_mode": output_mode,
                "sources_count": len(sources),
                "progress": 100,
                "timestamp": datetime.now().isoformat()
            }) + "\n"

        except Exception as e:
            logger.error(f"Research error: {e}", exc_info=True)
            session.status = "failed"
            session.updated_at = datetime.now().isoformat()
            self.session_repo.update_session(session)
            await self.file_backend.save_session_snapshot(session)

            yield json.dumps({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }) + "\n"

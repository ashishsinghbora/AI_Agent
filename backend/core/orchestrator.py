"""Research Orchestrator: Main agent coordinating all research tasks"""

import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from .utils import (
    build_excerpt,
    check_internet,
    detect_conflicts,
    extract_keywords,
)

logger = logging.getLogger(__name__)

# ── Speed profiles ────────────────────────────────────────────────────────────

_SPEED_PROFILES: Dict[str, Dict[str, Any]] = {
    "fast": {
        "response_temperature": 0.35,
        "response_max_tokens": 900,
        "context_top_k": 2,
        "fetch_timeout": 10.0,
        "source_cap": 3,
        "response_style": (
            "Answer quickly and clearly in short bullet points. "
            "Keep it concise and practical."
        ),
    },
    "balanced": {
        "response_temperature": 0.5,
        "response_max_tokens": 1300,
        "context_top_k": 3,
        "fetch_timeout": 14.0,
        "source_cap": 5,
        "response_style": "Answer clearly with moderate detail and practical structure.",
    },
    "deep": {
        "response_temperature": 0.65,
        "response_max_tokens": 1800,
        "context_top_k": 4,
        "fetch_timeout": 20.0,
        "source_cap": 8,
        "response_style": "Answer with depth, structure, and practical details.",
    },
}


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
        file_backend,
        web_researcher=None,
    ):
        """
        Initialize orchestrator with dependencies (Dependency Injection).

        Args:
            config_manager: ConfigManager instance
            ollama_manager: OllamaManager for model inference
            web_fetcher_agent: WebFetcherAgent for smart fetching
            response_synthesizer: ResponseSynthesizer for formatting
            vector_store: VectorStore for persistence
            resource_manager: ResourceManager for resource allocation
            session_repository: SessionRepository for DB persistence
            file_backend: FileBackend for JSON snapshots
            web_researcher: Optional WebResearcher for internet check
        """
        self.config = config_manager
        self.ollama = ollama_manager
        self.fetcher_agent = web_fetcher_agent
        self.synthesizer = response_synthesizer
        self.vector_store = vector_store
        self.resource_manager = resource_manager
        self.session_repo = session_repository
        self.file_backend = file_backend
        self._web_researcher = web_researcher  # optional; used for internet check

    async def research(
        self,
        query: str,
        output_mode: str = "quick",
        max_sources: int = 5,
        cpu_budget_percent: float = 80.0,
        use_thinking: bool = True,
        thinking_chars: int = 180,
        preferred_domains: Optional[List[str]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        speed_mode: str = "fast",
    ) -> AsyncGenerator[str, None]:
        """
        Execute complete research flow with streaming events.

        Yields:
            JSON event strings (one per line, NDJSON format)
        """
        from .persistence import ResearchSession
        from .synthesizer import OutputMode, ResponseSynthesizer

        profile = _SPEED_PROFILES.get(speed_mode.lower(), _SPEED_PROFILES["fast"])
        effective_max_sources = min(max(1, max_sources), profile["source_cap"])
        effective_thinking_chars = max(0, min(thinking_chars, 800))

        session_id = datetime.now().isoformat()
        chat_history = chat_history or []
        preferred_domains = preferred_domains or []

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
            metadata={"cpu_budget": cpu_budget_percent, "speed_mode": speed_mode},
        )
        self.session_repo.create_session(session)

        try:
            # Phase 1: Status
            yield json.dumps({
                "type": "status",
                "message": f"Starting research: {query[:50]}...",
                "progress": 5,
            }) + "\n"

            # Phase 2: Thinking
            accumulated_thinking = ""
            if use_thinking and effective_thinking_chars > 0:
                yield json.dumps({
                    "type": "thinking_start",
                    "timestamp": datetime.now().isoformat(),
                }) + "\n"

                thinking_prompt = (
                    "Create a very short research plan in at most 2 bullets and "
                    "at most 25 words total. Do not explain in detail.\n\n"
                    f"Query: {query}"
                )

                emitted_chars = 0
                was_truncated = False
                async for chunk in self.ollama.generate_streaming(
                    prompt=thinking_prompt,
                    model="gemma2:2b",
                    temperature=0.2,
                    max_tokens=80,
                ):
                    remaining = effective_thinking_chars - emitted_chars
                    if remaining <= 0:
                        was_truncated = True
                        break
                    clipped = chunk[:remaining]
                    emitted_chars += len(clipped)
                    accumulated_thinking += clipped
                    yield json.dumps({"type": "thinking", "content": clipped}) + "\n"

                if was_truncated:
                    yield json.dumps({"type": "thinking", "content": " ..."}) + "\n"

                session.thinking = accumulated_thinking
                yield json.dumps({
                    "type": "thinking_end",
                    "timestamp": datetime.now().isoformat(),
                }) + "\n"

            # Phase 3: Internet check
            yield json.dumps({
                "type": "status",
                "message": "Checking internet access via terminal...",
                "progress": 10,
            }) + "\n"

            if self._web_researcher and hasattr(self._web_researcher, "check_internet_via_terminal"):
                internet_status = await self._web_researcher.check_internet_via_terminal()
            else:
                internet_status = await check_internet()

            yield json.dumps({"type": "internet_check", **internet_status}) + "\n"
            yield json.dumps({
                "type": "status",
                "message": (
                    "Internet check passed. Starting web research..."
                    if internet_status.get("online")
                    else "Internet check failed. Continuing with available methods..."
                ),
                "progress": 15,
            }) + "\n"

            # Phase 4: Web research
            yield json.dumps({
                "type": "research_start",
                "message": "Searching the web for relevant information...",
                "progress": 20,
            }) + "\n"

            self.resource_manager.allocate_resources(
                max_sources=effective_max_sources,
                cpu_budget_percent=cpu_budget_percent,
            )

            did_search, raw_sources = await self.fetcher_agent.smart_fetch(
                query=query,
                user_max_sources=effective_max_sources,
                force_search=False,
                request_timeout=profile["fetch_timeout"],
            )

            # Enrich sources with excerpt + keywords for the client
            sources_for_client = [
                {
                    "title": s.get("title"),
                    "url": s.get("url"),
                    "snippet": s.get("snippet", ""),
                    "excerpt": build_excerpt(s.get("content", "")) or s.get("snippet", ""),
                    "keywords": extract_keywords(
                        s.get("content", "") or s.get("snippet", "")
                    ),
                }
                for s in raw_sources
            ]

            if did_search:
                yield json.dumps({
                    "type": "sources_found",
                    "sources": sources_for_client,
                    "count": len(sources_for_client),
                    "progress": 30,
                }) + "\n"
                session.sources = sources_for_client
                session.findings_count = len(sources_for_client)

            # Phase 5: Store findings + per-source crawl events
            yield json.dumps({
                "type": "status",
                "message": "Processing and storing research findings...",
                "progress": 50,
            }) + "\n"

            for idx, source in enumerate(raw_sources, start=1):
                crawl_excerpt = (
                    build_excerpt(source.get("content", "")) or source.get("snippet", "")
                )
                crawl_keywords = extract_keywords(
                    source.get("content", "") or source.get("snippet", "")
                )
                yield json.dumps({
                    "type": "crawl_update",
                    "index": idx,
                    "total": len(raw_sources),
                    "title": source.get("title"),
                    "url": source.get("url"),
                    "excerpt": crawl_excerpt,
                    "keywords": crawl_keywords,
                }) + "\n"

                await self.vector_store.add_document(
                    content=source.get("content", ""),
                    metadata={
                        "url": source.get("url"),
                        "title": source.get("title"),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # Conflict detection
            conflicts = detect_conflicts(raw_sources)
            if conflicts:
                yield json.dumps({
                    "type": "conflict_alert",
                    "message": "Conflicting data detected across sources.",
                    "conflicts": conflicts,
                    "progress": 45,
                }) + "\n"

            # Phase 6: Generate response
            yield json.dumps({
                "type": "status",
                "message": "Generating comprehensive response...",
                "progress": 70,
            }) + "\n"

            context_docs = await self.vector_store.search(
                query, top_k=profile["context_top_k"]
            )
            context_str = "\n".join([
                f"- {doc.get('metadata', {}).get('title', 'Doc')}: "
                f"{doc.get('content', '')[:200]}..."
                for doc in context_docs
            ])

            full_prompt = (
                f"Based on this research about '{query}':\n\n"
                f"Research Context:\n{context_str}\n\n"
                f"{profile['response_style']}\nFormat with markdown."
            )

            accumulated_response = ""
            yield json.dumps({"type": "response_start", "progress": 75}) + "\n"

            async for chunk in self.ollama.generate_streaming(
                prompt=full_prompt,
                model="gemma2:2b",
                temperature=profile["response_temperature"],
                max_tokens=profile["response_max_tokens"],
            ):
                accumulated_response += chunk
                yield json.dumps({"type": "response", "content": chunk}) + "\n"

            # Append source links to the response body
            if raw_sources:
                source_lines = ["", "", "### Sources"]
                for idx, src in enumerate(raw_sources, 1):
                    title = src.get("title") or f"Source {idx}"
                    url = src.get("url")
                    if url:
                        source_lines.append(f"- [{title}]({url})")
                source_section = "\n".join(source_lines)
            else:
                source_section = "\n\n### Sources\n- No external sources found for this query."

            accumulated_response += source_section
            yield json.dumps({"type": "response", "content": source_section}) + "\n"

            # Concept graph
            concept_terms = extract_keywords(accumulated_response, max_terms=7)
            if concept_terms:
                graph = {
                    "nodes": [
                        {"id": "root", "label": query, "type": "root"},
                        *[
                            {"id": term, "label": term.title(), "type": "concept"}
                            for term in concept_terms
                        ],
                    ],
                    "edges": [{"from": "root", "to": term} for term in concept_terms],
                }
                yield json.dumps({"type": "concept_graph", "graph": graph}) + "\n"

            session.response = accumulated_response

            # Phase 7: Synthesize into requested output format
            logger.info(f"Synthesizing in {output_mode} mode")
            try:
                output_mode_enum = OutputMode[output_mode.upper()]
            except (KeyError, AttributeError):
                output_mode_enum = OutputMode.QUICK

            session.response = ResponseSynthesizer.synthesize(
                mode=output_mode_enum,
                query=query,
                thinking=accumulated_thinking,
                response=accumulated_response,
                sources=sources_for_client,
            )

            # Phase 8: Persist
            yield json.dumps({
                "type": "status",
                "message": "Saving research...",
                "progress": 90,
            }) + "\n"

            session.status = "completed"
            session.updated_at = datetime.now().isoformat()
            self.session_repo.update_session(session)
            await self.file_backend.save_session_snapshot(session)

            yield json.dumps({
                "type": "research_complete",
                "message": "Research complete!",
                "session_id": session_id,
                "output_mode": output_mode,
                "sources_count": len(raw_sources),
                "sources": sources_for_client,
                "progress": 100,
                "timestamp": datetime.now().isoformat(),
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
                "timestamp": datetime.now().isoformat(),
            }) + "\n"

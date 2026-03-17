#!/usr/bin/env python3
"""
Research Student AI Agent - FastAPI Backend (v2)

Thin HTTP layer that wires core modules together and exposes REST endpoints.
All research logic lives in core/orchestrator.py.
"""

import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, List, Optional
import psutil
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from backend.core.config import ConfigManager
from backend.core.fetcher import IWebFetcher, WebFetcherAgent
from backend.core.orchestrator import ResearchOrchestrator
from backend.core.persistence import SessionRepository, FileBackend
from backend.core.resources import ResourceManager
from backend.core.synthesizer import ResponseSynthesizer
from backend.core.utils import build_learning_pack, extract_pdf_text
from backend.tools import (
    FileManager,
    GeminiStreamManager,
    ResearchSummarizer,
    TerminalExecutor,
    VectorStore,
    WebResearcher,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SESSION_NOT_FOUND = "Session not found"


# ── Adapter: tools.WebResearcher → core.fetcher.IWebFetcher ──────────────────

class _WebResearcherAdapter(IWebFetcher):
    """Bridges the concrete WebResearcher to the IWebFetcher abstraction."""

    def __init__(self, researcher: WebResearcher):
        self._researcher = researcher

    async def fetch(self, query: str, max_sources: int, timeout: float, **kwargs) -> list:
        return await self._researcher.research(
            query=query,
            max_sources=max_sources,
            request_timeout=timeout,
            preferred_domains=kwargs.get("preferred_domains", []),
        )


# ── Module-level singletons (populated in lifespan) ──────────────────────────

_config: Optional[ConfigManager] = None
_session_repo: Optional[SessionRepository] = None
_orchestrator: Optional[ResearchOrchestrator] = None
_file_manager: Optional[FileManager] = None
_summarizer: Optional[ResearchSummarizer] = None
_terminal_executor: Optional[TerminalExecutor] = None
_backend_env_path = Path(__file__).resolve().parent / ".env"


def _find_env_key_index(lines: List[str], pattern: re.Pattern[str]) -> int:
    """Return index of env assignment line, or -1 when absent."""
    for idx, line in enumerate(lines):
        if pattern.match(line):
            return idx
    return -1


def _write_env_lines(file_path: Path, lines: List[str]) -> None:
    """Persist normalized env lines to disk with trailing newline."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines).strip()
    file_path.write_text(f"{content}\n" if content else "")


def _upsert_env_value(file_path: Path, key: str, value: str) -> None:
    """Insert/update/remove a key in a .env-style file."""
    lines = file_path.read_text().splitlines() if file_path.exists() else []
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")

    existing_index = _find_env_key_index(lines, pattern)

    if value:
        assignment = f"{key}={value}"
        if existing_index >= 0:
            lines[existing_index] = assignment
        else:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append(assignment)
    elif existing_index >= 0:
        del lines[existing_index]

    _write_env_lines(file_path, lines)


def _parse_cors_origins() -> List[str]:
    """Parse comma-separated allowed origins from env."""
    raw = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:3000"]


@asynccontextmanager
async def lifespan(application: FastAPI):
    global _config, _session_repo, _orchestrator, _file_manager, _summarizer, _terminal_executor

    try:
        from dotenv import load_dotenv
        load_dotenv(_backend_env_path, override=True)
    except ImportError:
        logger.warning("python-dotenv unavailable; backend .env loading skipped")

    _config = ConfigManager()
    _session_repo = SessionRepository(_config.db_path)
    file_backend = FileBackend(_config.research_notes_path)

    vector_store = VectorStore(
        collection_name="research_findings",
        persist_dir=str(_config.chroma_persist_dir),
    )
    web_researcher = WebResearcher()
    fetcher_agent = WebFetcherAgent(_WebResearcherAdapter(web_researcher))
    response_synthesizer = ResponseSynthesizer()
    resource_manager = ResourceManager(_config)
    llm_manager = GeminiStreamManager(api_key=os.getenv("GEMINI_API_KEY", ""))

    _orchestrator = ResearchOrchestrator(
        config_manager=_config,
        ollama_manager=llm_manager,
        web_fetcher_agent=fetcher_agent,
        response_synthesizer=response_synthesizer,
        vector_store=vector_store,
        resource_manager=resource_manager,
        session_repository=_session_repo,
        file_backend=file_backend,
        web_researcher=web_researcher,
    )

    _file_manager = FileManager(base_path=str(_config.research_notes_path))
    _summarizer = ResearchSummarizer()
    _terminal_executor = TerminalExecutor()

    logger.info("Research Agent started — DB: %s", _config.db_path)
    yield
    logger.info("Research Agent shutting down")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title= "Research Agent API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ResearchQuery(BaseModel):
    query: str
    max_sources: int = 5
    use_thinking_model: bool = True
    speed_mode: str = "fast"
    output_mode: str = "quick"
    thinking_chars: int = 180
    cpu_budget_percent: float = 80.0
    preferred_domains: List[str] = []
    chat_history: List[ChatMessage] = []
    gemini_api_key: str = ""


class GeminiKeyPayload(BaseModel):
    api_key: str = ""
    persist_to_env: bool = True


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/research")
async def research(query_data: ResearchQuery):
    """Streaming research endpoint — delegates to ResearchOrchestrator."""

    # Accept an API key from the client payload so research can run even
    # when backend runtime env has not been synced yet.
    provided_key = (query_data.gemini_api_key or "").strip()
    if provided_key:
        os.environ["GEMINI_API_KEY"] = provided_key
        if _orchestrator and hasattr(_orchestrator, "ollama"):
            _orchestrator.ollama.api_key = provided_key

    async def event_generator():
        async for event in _orchestrator.research(
            query=query_data.query,
            output_mode=query_data.output_mode,
            max_sources=query_data.max_sources,
            cpu_budget_percent=query_data.cpu_budget_percent,
            use_thinking=query_data.use_thinking_model,
            thinking_chars=query_data.thinking_chars,
            preferred_domains=query_data.preferred_domains,
            chat_history=[
                {"role": m.role, "content": m.content}
                for m in query_data.chat_history
            ],
            speed_mode=query_data.speed_mode,
        ):
            yield event

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.post(
    "/api/config/gemini-key",
    responses={500: {"description": "Failed to update backend env"}},
)
async def set_gemini_key(payload: GeminiKeyPayload):
    """Save GEMINI_API_KEY to runtime environment and optional backend/.env."""
    cleaned_key = payload.api_key.strip()

    if cleaned_key:
        os.environ["GEMINI_API_KEY"] = cleaned_key
    else:
        os.environ.pop("GEMINI_API_KEY", None)

    if _orchestrator and hasattr(_orchestrator, "ollama"):
        _orchestrator.ollama.api_key = cleaned_key

    persisted = False
    if payload.persist_to_env:
        try:
            _upsert_env_value(_backend_env_path, "GEMINI_API_KEY", cleaned_key)
            persisted = True
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"Failed to update backend env: {exc}") from exc

    return JSONResponse({
        "status": "updated" if cleaned_key else "cleared",
        "persisted_to_env": persisted,
        "env_path": str(_backend_env_path),
    })


@app.get("/api/system-stats")
async def system_stats():
    """Real-time system resource stats."""
    vm = psutil.virtual_memory()
    return JSONResponse({
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory": {
            "used": vm.used / (1024 ** 3),
            "total": vm.total / (1024 ** 3),
            "percent": vm.percent,
        },
        "timestamp": datetime.now().isoformat(),
    })


@app.get("/api/sessions")
async def get_sessions():
    """List all research sessions from the database."""
    sessions = _session_repo.list_sessions(limit=100)
    return JSONResponse({
        "sessions": [
            {
                "session_id": s.session_id,
                "query": s.query,
                "started_at": s.created_at,
                "findings_count": s.findings_count,
                "status": s.status,
                "output_mode": s.output_mode,
            }
            for s in sessions
        ]
    })


@app.get(
    "/api/sessions/{session_id}",
    responses={404: {"description": "Session not found"}},
)
async def get_session(session_id: str):
    """Get a specific research session."""
    session = _session_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)
    return JSONResponse({
        "session_id": session.session_id,
        "query": session.query,
        "started_at": session.created_at,
        "findings": session.sources,
        "findings_count": session.findings_count,
        "status": session.status,
        "output_mode": session.output_mode,
        "thinking": session.thinking,
        "response": session.response,
        "metadata": session.metadata,
    })


@app.delete(
    "/api/sessions/{session_id}",
    responses={404: {"description": "Session not found"}},
)
async def delete_session(session_id: str):
    """Delete a research session."""
    success = _session_repo.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)
    return JSONResponse({"deleted": session_id})


@app.post(
    "/api/export/{session_id}",
    responses={404: {"description": "Session not found"}},
)
async def export_session(
    session_id: str,
    export_format: Annotated[str, Query(alias="format")] = "markdown",
):
    """Export a research session as PDF, Markdown, or Learning Pack."""
    session = _session_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND)

    if export_format == "pdf":
        pdf_path = await _summarizer.generate_pdf(
            query=session.query,
            findings=session.sources,
            session_id=session_id,
        )
        return JSONResponse({"path": pdf_path, "format": "pdf"})

    if export_format == "learning-pack":
        pack_content = build_learning_pack(session.query, session.response, session.sources)
        pack_path = await _file_manager.create_file(
            filename=f"learning_pack_{session_id}.md",
            content=pack_content,
        )
        return JSONResponse({"path": pack_path, "format": "learning-pack"})

    md_path = await _file_manager.save_research(
        filename=f"export_{session_id}.md",
        content=session.response,
        query=session.query,
        sources=session.sources,
    )
    return JSONResponse({"path": md_path, "format": "markdown"})


@app.post(
    "/api/ingest",
    responses={400: {"description": "Invalid or unsupported file"}},
)
async def ingest_file(file: Annotated[UploadFile, File(...)]):
    """Ingest a file into the vector store."""
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    payload = await file.read()

    text_content = ""
    if file.content_type and file.content_type.startswith("text/"):
        text_content = payload.decode("utf-8", errors="ignore")
    elif suffix in {".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".csv", ".yml", ".yaml"}:
        text_content = payload.decode("utf-8", errors="ignore")
    elif suffix == ".pdf":
        text_content = extract_pdf_text(payload)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")


    if not text_content.strip():
        raise HTTPException(status_code=400, detail="File is empty or could not be read")

    await _orchestrator.vector_store.add_document(
        content=text_content,
        metadata={
            "filename": filename,
            "source": "upload",
            "timestamp": datetime.now().isoformat(),
        },
    )
    return JSONResponse({"status": "embedded", "filename": filename, "chars": len(text_content)})

@app.post(
    "/api/execute",
    responses={403: {"description": "Command not allowed"}},
)
async def execute_command(command_data: dict):
    """Execute restricted terminal commands."""
    cmd = command_data.get("command", "")
    # Validate by checking only the first token (the command itself)
    first_token = cmd.split()[0] if cmd.split() else ""
    safe_commands = {"ls", "pwd", "whoami", "uname", "df", "top", "ps", "grep", "find"}
    if first_token not in safe_commands:
        raise HTTPException(status_code=403, detail="Command not allowed")
    result = await _terminal_executor.execute(cmd)
    return JSONResponse(result)



@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("FASTAPI_HOST", "127.0.0.1"),
        port=int(os.getenv("FASTAPI_PORT", "8000")),
        reload=False,
    )

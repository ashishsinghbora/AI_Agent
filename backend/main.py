#!/usr/bin/env python3
"""
Research Student AI Agent - FastAPI Backend
Handles agentic loop, Ollama integration, and web research capabilities
"""

import asyncio
import json
import logging
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import psutil
from tools import (
    OllamaManager,
    VectorStore,
    FileManager,
    WebResearcher,
    TerminalExecutor,
    ResearchSummarizer
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Research Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
ollama = OllamaManager(model_primary="deepseek-r1:7b", model_fallback="gemma2:2b")
vector_store = VectorStore(collection_name="research_findings")
file_manager = FileManager(base_path="/home/ashu/research_notes")
web_researcher = WebResearcher()
terminal_executor = TerminalExecutor()
summarizer = ResearchSummarizer()

# Data models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ResearchQuery(BaseModel):
    query: str
    max_sources: int = 5
    use_thinking_model: bool = True
    speed_mode: str = "fast"  # fast | balanced | deep
    thinking_chars: int = 180
    preferred_domains: list[str] = []
    chat_history: list[ChatMessage] = []

class ResearchSession(BaseModel):
    session_id: str
    query: str
    started_at: datetime
    findings: list[dict] = []
    chat_history: list[ChatMessage] = []

# In-memory storage for sessions
research_sessions = {}


def _build_excerpt(text: str, max_len: int = 320) -> str:
    if not text:
        return ""
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if not chunks:
        chunks = [line.strip() for line in text.split("\n") if line.strip()]
    excerpt = chunks[0] if chunks else text.strip()
    if len(excerpt) > max_len:
        excerpt = excerpt[: max_len - 3].rstrip() + "..."
    return excerpt


def _extract_keywords(text: str, max_terms: int = 6) -> list[str]:
    if not text:
        return []
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
        "you", "your", "into", "about", "can", "will", "their", "they", "has", "have",
        "had", "not", "but", "use", "using", "used", "what", "when", "where", "how",
        "why", "who", "which", "more", "most", "than", "over", "also", "its", "our",
        "such", "these", "those", "may", "might", "been", "being", "like", "within"
    }
    freq = {}
    for token in tokens:
        if token in stopwords:
            continue
        freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [word for word, _count in ranked[:max_terms]]


def _detect_conflicts(sources: list[dict]) -> list[dict]:
    pattern = re.compile(r"\b(\d+(?:\.\d+)?)\s*(nm|nanometer|%|percent|ghz|mhz|gb|tb)\b", re.I)
    seen = {}
    for source in sources:
        content = source.get("content", "") or ""
        for match in pattern.finditer(content[:2000]):
            value = match.group(1)
            unit = match.group(2).lower()
            key = unit
            seen.setdefault(key, {}).setdefault(value, []).append(
                {
                    "title": source.get("title"),
                    "url": source.get("url")
                }
            )

    conflicts = []
    for unit, values in seen.items():
        if len(values) > 1:
            conflicts.append({
                "unit": unit,
                "values": [
                    {"value": value, "sources": sources_list[:2]}
                    for value, sources_list in values.items()
                ]
            })
    return conflicts


def _build_learning_pack(query: str, response: str, sources: list[dict]) -> str:
    clean_response = response.split("### Sources", 1)[0].strip()
    sentences = re.split(r"(?<=[.!?])\s+", clean_response)
    summary = " ".join(sentences[:3]).strip()

    keywords = _extract_keywords(clean_response, max_terms=8)
    terms_section = "\n".join([f"- **{term.title()}**: {term} is discussed in the research findings." for term in keywords])

    quiz_terms = keywords[:3] if keywords else ["this topic"]
    quiz_questions = "\n".join([
        f"1. What is {quiz_terms[0].title()} and why does it matter in this context?",
        f"2. How would you apply {quiz_terms[1].title()} in a real-world scenario?" if len(quiz_terms) > 1 else "2. What is the most important takeaway from the research?",
        f"3. What assumptions or limitations surround {quiz_terms[2].title()}?" if len(quiz_terms) > 2 else "3. Which source would you trust most and why?"
    ])

    source_list = "\n".join([
        f"- [{source.get('title', 'Source')}]({source.get('url', '#')})"
        for source in sources[:5]
    ])

    return f"""# Learning Pack: {query}

## Summary
{summary or clean_response[:400]}

## Key Terms
{terms_section or "- No key terms detected."}

## Quick Quiz
{quiz_questions}

## Sources
{source_list or "- No sources available."}
"""


def _extract_pdf_text(file_bytes: bytes) -> str:
    if not shutil.which("pdftotext"):
        return ""

    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "upload.pdf"
        txt_path = Path(temp_dir) / "upload.txt"
        pdf_path.write_bytes(file_bytes)
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0 or not txt_path.exists():
            return ""
        return txt_path.read_text(errors="ignore")

# ==================== STREAMING AGENT LOOP ====================

async def agent_research_loop(
    query: str,
    chat_history: list[ChatMessage],
    use_thinking_model: bool = True,
    max_sources: int = 5,
    speed_mode: str = "fast",
    thinking_chars: int = 180,
    preferred_domains: Optional[list[str]] = None
) -> AsyncGenerator[str, None]:
    """
    Main research agent loop with streaming thoughts and actions
    Yields JSON strings for frontend consumption
    """
    
    session_id = datetime.now().isoformat()
    session = ResearchSession(
        session_id=session_id,
        query=query,
        started_at=datetime.now(),
        chat_history=chat_history
    )
    research_sessions[session_id] = session
    
    try:
        normalized_speed_mode = (speed_mode or "fast").lower()
        if normalized_speed_mode not in {"fast", "balanced", "deep"}:
            normalized_speed_mode = "fast"

        # Speed profiles keep behavior predictable while allowing a fast default.
        if normalized_speed_mode == "fast":
            effective_max_sources = max(1, min(max_sources, 3))
            response_temperature = 0.35
            response_max_tokens = 900
            context_top_k = 2
            fetch_chars = 800
            fetch_timeout = 10
        elif normalized_speed_mode == "deep":
            effective_max_sources = max(1, min(max_sources, 8))
            response_temperature = 0.65
            response_max_tokens = 1800
            context_top_k = 4
            fetch_chars = 1600
            fetch_timeout = 20
        else:
            effective_max_sources = max(1, min(max_sources, 5))
            response_temperature = 0.5
            response_max_tokens = 1300
            context_top_k = 3
            fetch_chars = 1200
            fetch_timeout = 14

        effective_thinking_chars = max(0, min(thinking_chars, 800))

        # Step 1: Stream thinking/reasoning
        yield json.dumps({
            "type": "thinking_start",
            "timestamp": datetime.now().isoformat()
        }) + "\n"
        
        # Use thinking model for deep reasoning
        if use_thinking_model and effective_thinking_chars > 0:
            thinking_response = ollama.generate_streaming(
                prompt=(
                    "Create a very short research plan in at most 2 bullets and at most 25 words total. "
                    "Do not explain in detail.\n\n"
                    f"Query: {query}"
                ),
                # Keep a lightweight model for lower latency and lower CPU heat.
                model="gemma2:2b",
                temperature=0.2,
                max_tokens=80
            )

            emitted_chars = 0
            was_truncated = False
            async for chunk in thinking_response:
                remaining = effective_thinking_chars - emitted_chars
                if remaining <= 0:
                    was_truncated = True
                    break

                clipped_chunk = chunk[:remaining]
                emitted_chars += len(clipped_chunk)
                if not clipped_chunk:
                    continue

                yield json.dumps({
                    "type": "thinking",
                    "content": clipped_chunk
                }) + "\n"

            if was_truncated:
                yield json.dumps({
                    "type": "thinking",
                    "content": " ..."
                }) + "\n"
        
        yield json.dumps({
            "type": "thinking_end",
            "timestamp": datetime.now().isoformat()
        }) + "\n"

        # Connectivity check via terminal before web research
        yield json.dumps({
            "type": "status",
            "message": "Checking internet access via terminal...",
            "progress": 10
        }) + "\n"

        internet_status = await web_researcher.check_internet_via_terminal()
        yield json.dumps({
            "type": "internet_check",
            "online": internet_status.get("online", False),
            "details": internet_status.get("details", "")
        }) + "\n"

        if internet_status.get("online", False):
            yield json.dumps({
                "type": "status",
                "message": "Internet check passed. Starting web research...",
                "progress": 15
            }) + "\n"
        else:
            yield json.dumps({
                "type": "status",
                "message": "Internet check failed. Continuing with available methods...",
                "progress": 15
            }) + "\n"
        
        # Step 2: Web research
        yield json.dumps({
            "type": "research_start",
            "message": "Searching the web for relevant information...",
            "progress": 20
        }) + "\n"
        
        sources = await web_researcher.research(
            query=query,
            max_sources=effective_max_sources,
            request_timeout=fetch_timeout,
            include_content_chars=fetch_chars,
            max_parallel_fetches=4,
            preferred_domains=preferred_domains
        )

        # Keep stream payload lightweight for faster frontend updates.
        sources_for_client = [
            {
                "title": source.get("title"),
                "url": source.get("url"),
                "snippet": source.get("snippet", ""),
                "excerpt": _build_excerpt(source.get("content", "")) or source.get("snippet", ""),
                "keywords": _extract_keywords(source.get("content", "") or source.get("snippet", ""))
            }
            for source in sources
        ]
        
        yield json.dumps({
            "type": "sources_found",
            "sources": sources_for_client,
            "count": len(sources),
            "progress": 30
        }) + "\n"

        # Persist source metadata for session list/findings counters.
        session.findings = sources_for_client
        
        # Step 3: Store findings in vector store
        yield json.dumps({
            "type": "status",
            "message": "Processing and storing research findings...",
            "progress": 50
        }) + "\n"
        
        for idx, source in enumerate(sources, start=1):
            crawl_excerpt = _build_excerpt(source.get("content", "")) or source.get("snippet", "")
            crawl_keywords = _extract_keywords(source.get("content", "") or source.get("snippet", ""))
            yield json.dumps({
                "type": "crawl_update",
                "index": idx,
                "total": len(sources),
                "title": source.get("title"),
                "url": source.get("url"),
                "excerpt": crawl_excerpt,
                "keywords": crawl_keywords
            }) + "\n"

            await vector_store.add_document(
                content=source.get("content", ""),
                metadata={
                    "url": source.get("url"),
                    "title": source.get("title"),
                    "timestamp": datetime.now().isoformat()
                }
            )

        conflicts = _detect_conflicts(sources)
        if conflicts:
            yield json.dumps({
                "type": "conflict_alert",
                "message": "Conflicting data detected across sources.",
                "conflicts": conflicts,
                "progress": 45
            }) + "\n"
        
        # Step 4: Generate response using context
        yield json.dumps({
            "type": "status",
            "message": "Generating comprehensive response...",
            "progress": 70
        }) + "\n"
        
        # Retrieve relevant context from vector store
        context = await vector_store.search(query=query, top_k=context_top_k)
        
        # Build prompt with context
        context_str = "\n".join([f"- {doc['metadata']['title']}: {doc['content'][:200]}..." 
                                  for doc in context])
        
        if normalized_speed_mode == "fast":
            response_style = "Answer quickly and clearly in short bullet points. Keep it concise and practical."
        elif normalized_speed_mode == "deep":
            response_style = "Answer with depth, structure, and practical details."
        else:
            response_style = "Answer clearly with moderate detail and practical structure."

        full_prompt = f"""Based on this research about '{query}':

Research Context:
{context_str}

{response_style}
Format with markdown."""
        
        # Stream the final response
        yield json.dumps({
            "type": "response_start",
            "progress": 75
        }) + "\n"
        
        response_stream = ollama.generate_streaming(
            prompt=full_prompt,
            model="gemma2:2b",
            temperature=response_temperature,
            max_tokens=response_max_tokens
        )
        
        full_response = ""
        async for chunk in response_stream:
            full_response += chunk
            yield json.dumps({
                "type": "response",
                "content": chunk
            }) + "\n"

        # Always append source links to the final response body.
        if sources:
            source_lines = ["", "", "### Sources"]
            for idx, source in enumerate(sources, 1):
                title = source.get("title") or f"Source {idx}"
                url = source.get("url")
                if url:
                    source_lines.append(f"- [{title}]({url})")
            source_section = "\n".join(source_lines)
        else:
            source_section = "\n\n### Sources\n- No external sources found for this query."

        full_response += source_section
        yield json.dumps({
            "type": "response",
            "content": source_section
        }) + "\n"

        concept_terms = _extract_keywords(full_response, max_terms=7)
        if concept_terms:
            graph = {
                "nodes": [
                    {"id": "root", "label": query, "type": "root"},
                    *[
                        {"id": term, "label": term.title(), "type": "concept"}
                        for term in concept_terms
                    ]
                ],
                "edges": [
                    {"from": "root", "to": term}
                    for term in concept_terms
                ]
            }
            yield json.dumps({
                "type": "concept_graph",
                "graph": graph
            }) + "\n"

        session.chat_history = [
            *chat_history,
            ChatMessage(
                role="assistant",
                content=full_response,
                timestamp=datetime.now()
            )
        ]
        
        # Step 5: Summary and storage
        yield json.dumps({
            "type": "status",
            "message": "Creating summary and saving research...",
            "progress": 85
        }) + "\n"
        
        # Save to local storage
        await file_manager.save_research(
            filename=f"research_{session_id.replace(':', '-')}.md",
            content=full_response,
            query=query,
            sources=sources
        )
        
        # Generate summary
        summary = await summarizer.create_summary(
            query=query,
            response=full_response,
            sources=sources
        )
        
        yield json.dumps({
            "type": "research_complete",
            "message": "Research complete!",
            "summary": summary,
            "sources": sources_for_client,
            "progress": 100,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }) + "\n"
        
    except Exception as e:
        logger.error(f"Error in research loop: {e}")
        yield json.dumps({
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }) + "\n"

# ==================== API ENDPOINTS ====================

@app.post("/api/research")
async def research(query_data: ResearchQuery):
    """Endpoint for streaming research responses"""
    
    async def event_generator():
        async for item in agent_research_loop(
            query=query_data.query,
            chat_history=query_data.chat_history,
            use_thinking_model=query_data.use_thinking_model,
            max_sources=query_data.max_sources,
            speed_mode=query_data.speed_mode,
            thinking_chars=query_data.thinking_chars,
            preferred_domains=query_data.preferred_domains
        ):
            yield item
    
    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson"
    )

@app.get("/api/system-stats")
async def system_stats():
    """Get real-time system stats"""
    return JSONResponse({
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory": {
            "used": psutil.virtual_memory().used / (1024**3),
            "total": psutil.virtual_memory().total / (1024**3),
            "percent": psutil.virtual_memory().percent
        },
        "timestamp": datetime.now().isoformat()
    })

@app.get("/api/sessions")
async def get_sessions():
    """Get all research sessions"""
    return JSONResponse({
        "sessions": [{
            "session_id": s.session_id,
            "query": s.query,
            "started_at": s.started_at.isoformat(),
            "findings_count": len(s.findings)
        } for s in research_sessions.values()]
    })

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get specific research session"""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = research_sessions[session_id]
    return JSONResponse({
        "session_id": session.session_id,
        "query": session.query,
        "started_at": session.started_at.isoformat(),
        "findings": session.findings,
        "chat_history": [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat() if m.timestamp else None}
            for m in session.chat_history
        ]
    })

@app.post("/api/export/{session_id}")
async def export_session(session_id: str, format: str = "markdown"):
    """Export research session as PDF or Markdown"""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = research_sessions[session_id]
    
    if format == "pdf":
        pdf_path = await summarizer.generate_pdf(
            query=session.query,
            findings=session.findings,
            session_id=session_id
        )
        return JSONResponse({"path": pdf_path, "format": "pdf"})
    elif format == "learning-pack":
        response_text = ""
        for message in reversed(session.chat_history):
            if message.role == "assistant":
                response_text = message.content
                break
        pack_content = _build_learning_pack(session.query, response_text, session.findings)
        pack_path = await file_manager.create_file(
            filename=f"learning_pack_{session_id}.md",
            content=pack_content
        )
        return JSONResponse({"path": pack_path, "format": "learning-pack"})
    else:
        md_path = await file_manager.save_research(
            filename=f"export_{session_id}.md",
            content=json.dumps(session.dict(), indent=2),
            query=session.query,
            sources=session.findings
        )
        return JSONResponse({"path": md_path, "format": "markdown"})


@app.post("/api/ingest")
async def ingest_file(file: UploadFile = File(...)):
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    payload = await file.read()

    text_content = ""
    if file.content_type and file.content_type.startswith("text/"):
        text_content = payload.decode("utf-8", errors="ignore")
    elif suffix in {".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".csv", ".yml", ".yaml"}:
        text_content = payload.decode("utf-8", errors="ignore")
    elif suffix == ".pdf":
        text_content = _extract_pdf_text(payload)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not text_content.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text. For PDFs, install poppler-utils (pdftotext)."
        )

    await vector_store.add_document(
        content=text_content,
        metadata={
            "filename": filename,
            "source": "upload",
            "timestamp": datetime.now().isoformat()
        }
    )

    return JSONResponse({
        "status": "embedded",
        "filename": filename,
        "chars": len(text_content)
    })

@app.post("/api/execute")
async def execute_command(command_data: dict):
    """Execute terminal commands (with restrictions)"""
    cmd = command_data.get("command", "")
    
    # Security: Only allow safe commands
    safe_commands = ["ls", "pwd", "whoami", "uname", "df", "top", "ps", "grep", "find"]
    
    if not any(cmd.startswith(safe_cmd) for safe_cmd in safe_commands):
        raise HTTPException(status_code=403, detail="Command not allowed")
    
    result = await terminal_executor.execute(cmd)
    return JSONResponse(result)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    ollama_status = await ollama.health_check()
    return JSONResponse({
        "status": "healthy",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

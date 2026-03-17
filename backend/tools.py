#!/usr/bin/env python3
"""
Research Agent Tools Module
Handles cloud LLM, headless web research, file management, etc.
"""

import asyncio
import logging
import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# Lightweight AI Agent Tools
from google.generativeai import configure, GenerativeModel
import trafilatura
from duckduckgo_search import DDGS
try:
    # Works when launched as a package (backend.main).
    from backend.report_builder import build_word_report
except ModuleNotFoundError as exc:
    # Fallback for direct execution from backend/ directory.
    if exc.name in {"backend", "backend.report_builder"}:
        from report_builder import build_word_report
    else:
        raise

# --- Gemini API (Cloud LLM) ---
_DEFAULT_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]


def _normalize_gemini_model_name(model_name: str) -> str:
    candidate = (model_name or "").strip()
    if not candidate:
        return ""
    if candidate.startswith("models/"):
        candidate = candidate.split("/", 1)[1]
    # Ignore non-Gemini names (e.g., local ollama aliases like gemma2:2b).
    if not candidate.startswith("gemini-"):
        return ""
    return candidate


def _build_gemini_model_candidates(preferred_model: str = "") -> List[str]:
    candidates: List[str] = []

    preferred = _normalize_gemini_model_name(preferred_model)
    env_model = _normalize_gemini_model_name(os.getenv("GEMINI_MODEL", ""))

    if preferred:
        candidates.append(preferred)
    if env_model:
        candidates.append(env_model)

    candidates.extend(_DEFAULT_GEMINI_MODELS)

    seen = set()
    unique_candidates: List[str] = []
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)
        unique_candidates.append(name)

    return unique_candidates


def _is_missing_model_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "not found for api version" in message
        or "not supported for generatecontent" in message
        or "404 models/" in message
        or "model not found" in message
    )


def gemini_ask(prompt: str, api_key: str, preferred_model: str = "") -> str:
    configure(api_key=api_key)

    last_error: Optional[Exception] = None
    for model_name in _build_gemini_model_candidates(preferred_model):
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            last_error = exc
            if _is_missing_model_error(exc):
                logger.warning("Gemini model '%s' unavailable, trying fallback.", model_name)
                continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("No Gemini model candidates available.")

# --- DuckDuckGo Search (Text Only) ---
def search_duckduckgo(query: str, max_results: int = 5) -> list:
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))

# --- Trafilatura Web Scraping (Headless, Text-Only) ---
def scrape_url_text(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    return trafilatura.extract(downloaded, include_comments=False, include_tables=False) or ""

# --- Report Generation (Word) ---
def generate_report(summary: str, sources: list, filename: str = "Research_Report.docx"):
    return build_word_report(summary, sources, filename)


class GeminiStreamManager:
    """Compatibility wrapper that provides a streaming model interface."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    async def generate_streaming(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.5,
        max_tokens: int = 1024,
    ):
        del temperature, max_tokens

        if not self.api_key:
            yield "GEMINI_API_KEY is not configured."
            return

        try:
            text = await asyncio.to_thread(
                gemini_ask,
                prompt,
                self.api_key,
                _normalize_gemini_model_name(model),
            )
        except Exception as exc:
            logger.error("Gemini request failed: %s", exc)
            yield f"Model request failed: {exc}"
            return

        chunk_size = 220
        for idx in range(0, len(text), chunk_size):
            yield text[idx:idx + chunk_size]


import hashlib

# Third-party imports - will be installed via setup.sh
try:
    import chromadb
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)


# ==================== VECTOR STORE (CHROMA DB) ====================

class VectorStore:
    """Manages ChromaDB vector store for research findings"""
    
    def __init__(self, collection_name: str = "research_findings", persist_dir: str = "/tmp/chroma"):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        
        if chromadb:
            try:
                # Use the new PersistentClient API (chromadb >= 0.4.0)
                self.client = chromadb.PersistentClient(path=persist_dir)
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except (AttributeError, TypeError):
                # Fallback to EphemeralClient for newer versions if PersistentClient fails
                try:
                    self.client = chromadb.EphemeralClient()
                    self.collection = self.client.get_or_create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                except Exception as e:
                    logger.error(f"ChromaDB initialization error: {e}")
                    self.collection = None
        else:
            self.collection = None
            logger.warning("ChromaDB not available, vector store disabled")
    
    async def add_document(self, content: str, metadata: Dict[str, Any]):
        """Add document to vector store"""
        if not self.collection:
            return
        
        doc_id = hashlib.sha256(content.encode()).hexdigest()
        
        try:
            await asyncio.to_thread(
                self.collection.add,
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata],
            )
            logger.info(f"Added document {doc_id} to vector store")
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search vector store for relevant documents"""
        if not self.collection:
            return []
        
        try:
            results = await asyncio.to_thread(
                self.collection.query,
                query_texts=[query],
                n_results=top_k,
            )
            
            documents = []
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
            
            return documents
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

# ==================== WEB RESEARCHER ====================

class WebResearcher:
    """Performs text-only web search and extraction."""

    async def check_internet_via_terminal(self) -> Dict[str, Any]:
        """Quick connectivity check used by the orchestrator."""
        start = time.perf_counter()
        try:
            sock = await asyncio.to_thread(socket.create_connection, ("1.1.1.1", 53), 3.0)
            sock.close()
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {"online": True, "method": "socket", "latency_ms": latency_ms}
        except OSError as exc:
            return {
                "online": False,
                "method": "socket",
                "latency_ms": None,
                "error": str(exc),
            }

    async def research(
        self,
        query: str,
        max_sources: int = 5,
        request_timeout: float = 12.0,
        preferred_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search and scrape a small set of relevant web sources."""
        del request_timeout

        preferred_domains = preferred_domains or []
        raw_results = await asyncio.to_thread(
            search_duckduckgo,
            query,
            max(max_sources * 2, max_sources),
        )

        normalized: List[Dict[str, Any]] = []
        for item in raw_results:
            url = item.get("href") or item.get("url") or ""
            if not url:
                continue

            if preferred_domains:
                host = urlparse(url).netloc.lower()
                if not any(domain.lower() in host for domain in preferred_domains):
                    continue

            normalized.append(
                {
                    "title": item.get("title") or "Untitled Source",
                    "url": url,
                    "snippet": item.get("body") or item.get("snippet") or "",
                }
            )
            if len(normalized) >= max_sources:
                break

        if not normalized and preferred_domains:
            for item in raw_results[:max_sources]:
                url = item.get("href") or item.get("url") or ""
                if not url:
                    continue
                normalized.append(
                    {
                        "title": item.get("title") or "Untitled Source",
                        "url": url,
                        "snippet": item.get("body") or item.get("snippet") or "",
                    }
                )

        sources: List[Dict[str, Any]] = []
        for item in normalized[:max_sources]:
            content = await asyncio.to_thread(scrape_url_text, item["url"])
            item["content"] = content or item["snippet"]
            sources.append(item)

        return sources



# ==================== FILE MANAGER ====================

class FileManager:
    """Manages local file operations in research_notes directory"""
    
    def __init__(self, base_path: str = "/home/ashu/research_notes"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def create_file(self, filename: str, content: str) -> str:
        """Create a new file"""
        file_path = self.base_path / filename
        await asyncio.to_thread(file_path.write_text, content)
        logger.info(f"Created file: {file_path}")
        return str(file_path)
    
    def read_file(self, filename: str) -> str:
        """Read a file"""
        file_path = self.base_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text()
    
    def update_file(self, filename: str, content: str) -> str:
        """Update existing file"""
        file_path = self.base_path / filename
        file_path.write_text(content)
        logger.info(f"Updated file: {file_path}")
        return str(file_path)
    
    def list_files(self) -> List[str]:
        """List all files in research_notes"""
        return [f.name for f in self.base_path.glob("*") if f.is_file()]
    
    async def save_research(
        self,
        filename: str,
        content: str,
        query: str,
        sources: List[Dict]
    ) -> str:
        """Save research with metadata"""
        
        markdown_content = f"""# Research: {query}

**Date**: {datetime.now().isoformat()}

## Summary
{content}

## Sources
"""
        
        for i, source in enumerate(sources, 1):
            markdown_content += f"\n{i}. [{source.get('title', 'Source')}]({source.get('url', '#')})"
        
        return await self.create_file(filename, markdown_content)

# ==================== TERMINAL EXECUTOR ====================

class TerminalExecutor:
    """Safely execute terminal commands"""
    
    ALLOWED_COMMANDS = [
        "ls", "pwd", "whoami", "uname", "df", "ps", "grep",
        "find", "cat", "head", "tail", "wc", "date", "free",
        "top", "uptime", "lsof", "netstat"
    ]
    
    async def execute(self, command: str) -> Dict[str, Any]:
        """Execute a terminal command safely"""
        
        # Validate command
        cmd_name = command.split()[0]
        if cmd_name not in self.ALLOWED_COMMANDS:
            return {
                "success": False,
                "error": f"Command '{cmd_name}' not allowed",
                "command": command
            }
        
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "success": True,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Command timed out",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

# ==================== RESEARCH SUMMARIZER ====================

class ResearchSummarizer:
    """Generate summaries and export research"""
    
    def create_summary(
        self,
        query: str,
        response: str,
        sources: List[Dict]
    ) -> Dict[str, Any]:
        """Create a structured summary"""
        
        return {
            "query": query,
            "response_length": len(response),
            "sources_count": len(sources),
            "key_sources": [
                {
                    "title": s.get("title"),
                    "url": s.get("url")
                }
                for s in sources[:3]
            ],
            "created_at": datetime.now().isoformat()
        }
    
    async def generate_pdf(
        self,
        query: str,
        findings: List[Dict],
        session_id: str,
    ) -> str:
        """Generate PDF export of research without blocking the event loop."""
        return await asyncio.to_thread(self._generate_pdf_sync, query, findings, session_id)

    def _generate_pdf_sync(
        self,
        query: str,
        findings: List[Dict],
        session_id: str
    ) -> str:
        """Generate PDF export of research"""
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            pdf_path = f"/tmp/research_{session_id}.pdf"
            c = canvas.Canvas(pdf_path, pagesize=letter)
            _, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"Research: {query}")
            
            # Content
            c.setFont("Helvetica", 10)
            y = height - 100
            
            for finding in findings:
                c.drawString(50, y, f"- {finding.get('title', 'Finding')}")
                y -= 20
                if y < 50:
                    c.showPage()
                    y = height - 50
            
            c.save()
            logger.info(f"Generated PDF: {pdf_path}")
            return pdf_path
        
        except ImportError:
            logger.warning("reportlab not available, skipping PDF generation")
            return ""
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return ""

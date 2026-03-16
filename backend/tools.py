#!/usr/bin/env python3
"""
Research Agent Tools Module
Handles Ollama, ChromaDB, Web Research, File Management, etc.
"""

import asyncio
import httpx
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import subprocess
import re
import shlex
from html import unescape
from html2text import html2text
import hashlib
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

# Third-party imports - will be installed via setup.sh
try:
    import chromadb
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)

# ==================== OLLAMA MANAGER ====================

class OllamaManager:
    """Manages Ollama model interactions"""
    
    def __init__(self, model_primary: str = "deepseek-r1:7b", model_fallback: str = "gemma2:2b"):
        self.base_url = "http://localhost:11434"
        self.model_primary = model_primary
        self.model_fallback = model_fallback
        self.client = httpx.AsyncClient(timeout=300)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "running",
                    "models_available": [m["name"] for m in models]
                }
            return {"status": "error", "message": "Ollama not responding"}
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def generate_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        """Generate response with streaming"""
        
        if model is None:
            model = self.model_primary
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": True,
                    "keep_alive": "5m"  # Keep model in RAM for 5 minutes
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback to simpler model
            if model != self.model_fallback:
                logger.info(f"Falling back to {self.model_fallback}")
                async for chunk in self.generate_streaming(
                    prompt=prompt,
                    model=self.model_fallback,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk

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
        
        doc_id = hashlib.md5(content.encode()).hexdigest()
        
        try:
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
            logger.info(f"Added document {doc_id} to vector store")
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search vector store for relevant documents"""
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
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
    """Handles web research using Crawl4AI or Tavily"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
    
    async def research(
        self,
        query: str,
        max_sources: int = 5,
        request_timeout: Optional[float] = None,
        include_content_chars: Optional[int] = None,
        max_parallel_fetches: Optional[int] = None
    ) -> List[Dict]:
        """
        Research the web using Tavily API
        Falls back to simple web scraping if API unavailable
        """
        sources = []

        effective_timeout = request_timeout if request_timeout is not None else 30
        effective_content_chars = include_content_chars if include_content_chars is not None else 2000
        effective_parallel = max(1, max_parallel_fetches or 1)
        
        # Try Tavily API (requires API key)
        tavily_key = self._get_env("TAVILY_API_KEY")
        if tavily_key:
            sources = await self._tavily_search(query, tavily_key, max_sources, effective_timeout)

        # Terminal-based fallback search (requested behavior)
        if not sources:
            sources = await self._terminal_web_search(query, max_sources, effective_timeout)
        
        # Fallback: Use DuckDuckGo search
        if not sources:
            sources = await self._duckduckgo_search(query, max_sources)
        
        # Enrich sources with content
        semaphore = asyncio.Semaphore(effective_parallel)

        async def enrich_source(source: Dict[str, Any]) -> Dict[str, Any]:
            try:
                async with semaphore:
                    content = await self._fetch_page_content(
                        source.get("url", ""),
                        request_timeout=effective_timeout,
                        max_chars=effective_content_chars
                    )
                source["content"] = content
            except Exception as e:
                logger.warning(f"Could not fetch content from {source.get('url')}: {e}")
            return source

        enriched_sources = []
        if sources:
            enriched_sources = await asyncio.gather(
                *(enrich_source(source) for source in sources[:max_sources])
            )
        
        return enriched_sources

    async def check_internet_via_terminal(self) -> Dict[str, Any]:
        """Check internet reachability using a terminal command."""
        command = "curl -I -s --max-time 10 https://duckduckgo.com | head -n 1"

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            line = (result.stdout or result.stderr).strip()
            online = result.returncode == 0 and any(code in line for code in ("200", "301", "302"))
            return {"online": online, "details": line}
        except Exception as e:
            logger.warning(f"Terminal internet check failed: {e}")
            return {"online": False, "details": str(e)}

    async def _terminal_web_search(
        self,
        query: str,
        max_results: int,
        request_timeout: Optional[float] = None
    ) -> List[Dict]:
        """Search the web via terminal curl against DuckDuckGo HTML endpoint."""
        search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        max_time = int(request_timeout) if request_timeout else 20
        max_time = max(5, min(max_time, 60))
        command = f"curl -L -A 'Mozilla/5.0' -s --max-time {max_time} {shlex.quote(search_url)}"

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 or not result.stdout:
                return []

            html = result.stdout
            pattern = r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL)

            parsed_results = []
            for href, title_html in matches:
                url = self._normalize_result_url(href)
                if not url:
                    continue

                title = re.sub(r"<[^>]+>", "", title_html)
                title = unescape(title).strip() or "Web result"

                parsed_results.append(
                    {
                        "title": title,
                        "url": url,
                        "snippet": ""
                    }
                )

                if len(parsed_results) >= max_results:
                    break

            return parsed_results
        except Exception as e:
            logger.warning(f"Terminal web search failed: {e}")
            return []
    
    async def _tavily_search(
        self,
        query: str,
        api_key: str,
        max_results: int,
        request_timeout: Optional[float] = None
    ) -> List[Dict]:
        """Search using Tavily API"""
        try:
            response = await self.client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True
                },
                timeout=request_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "snippet": result.get("content")
                    }
                    for result in data.get("results", [])
                ]
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
        
        return []
    
    async def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict]:
        """Fallback: DuckDuckGo search"""
        try:
            # Using duckduckgo-search library
            from duckduckgo_search import DDGS
            
            ddgs = DDGS()
            results = ddgs.text(query, max_results=max_results)
            
            return [
                {
                    "title": r.get("title"),
                    "url": r.get("href"),
                    "snippet": r.get("body")
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return []
    
    async def _fetch_page_content(
        self,
        url: str,
        request_timeout: Optional[float] = None,
        max_chars: int = 2000
    ) -> str:
        """Fetch and convert webpage to text"""
        try:
            response = await self.client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
                timeout=request_timeout
            )
            if response.status_code == 200:
                # Convert HTML to markdown
                text_content = html2text(response.text)
                return text_content[:max_chars]  # Limit content size
            return ""
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""

    @staticmethod
    def _normalize_result_url(href: str) -> Optional[str]:
        """Normalize direct and DuckDuckGo redirect URLs to clean http(s) links."""
        href = unescape(href or "").strip()
        if not href:
            return None

        # Drop ad/tracking endpoints from search results.
        if "duckduckgo.com/y.js" in href or "bing.com/aclick" in href:
            return None

        if href.startswith("//"):
            href = f"https:{href}"

        if href.startswith("/"):
            href = f"https://duckduckgo.com{href}"

        if "duckduckgo.com/l/?" in href:
            parsed = urlparse(href)
            uddg = parse_qs(parsed.query).get("uddg")
            if uddg:
                clean = unquote(uddg[0])
                if "bing.com/aclick" in clean:
                    return None
                return clean if clean.startswith("http") else None

        return href if href.startswith("http://") or href.startswith("https://") else None
    
    @staticmethod
    def _get_env(key: str) -> Optional[str]:
        """Get environment variable"""
        import os
        return os.getenv(key)

# ==================== FILE MANAGER ====================

class FileManager:
    """Manages local file operations in research_notes directory"""
    
    def __init__(self, base_path: str = "/home/ashu/research_notes"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def create_file(self, filename: str, content: str) -> str:
        """Create a new file"""
        file_path = self.base_path / filename
        file_path.write_text(content)
        logger.info(f"Created file: {file_path}")
        return str(file_path)
    
    async def read_file(self, filename: str) -> str:
        """Read a file"""
        file_path = self.base_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text()
    
    async def update_file(self, filename: str, content: str) -> str:
        """Update existing file"""
        file_path = self.base_path / filename
        file_path.write_text(content)
        logger.info(f"Updated file: {file_path}")
        return str(file_path)
    
    async def list_files(self) -> List[str]:
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
    
    async def create_summary(
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
        session_id: str
    ) -> str:
        """Generate PDF export of research"""
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            pdf_path = f"/tmp/research_{session_id}.pdf"
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            
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

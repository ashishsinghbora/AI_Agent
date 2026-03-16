"""Shared utility functions for research processing"""

import asyncio
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ── Text helpers ──────────────────────────────────────────────────────────────

def build_excerpt(text: str, max_len: int = 320) -> str:
    """Extract a short excerpt from page content."""
    if not text:
        return ""
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if not chunks:
        chunks = [line.strip() for line in text.split("\n") if line.strip()]
    excerpt = chunks[0] if chunks else text.strip()
    if len(excerpt) > max_len:
        excerpt = excerpt[: max_len - 3].rstrip() + "..."
    return excerpt


def extract_keywords(text: str, max_terms: int = 6) -> List[str]:
    """Extract top keywords from text, ignoring common stopwords."""
    if not text:
        return []
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
        "you", "your", "into", "about", "can", "will", "their", "they", "has", "have",
        "had", "not", "but", "use", "using", "used", "what", "when", "where", "how",
        "why", "who", "which", "more", "most", "than", "over", "also", "its", "our",
        "such", "these", "those", "may", "might", "been", "being", "like", "within",
    }
    freq: Dict[str, int] = {}
    for token in tokens:
        if token not in stopwords:
            freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [word for word, _ in ranked[:max_terms]]


def detect_conflicts(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect conflicting numeric values across sources."""
    pattern = re.compile(r"\b(\d+(?:\.\d+)?)\s*(nm|nanometer|%|percent|ghz|mhz|gb|tb)\b", re.I)
    seen: Dict[str, Dict[str, List]] = {}
    for source in sources:
        content = source.get("content", "") or ""
        for match in pattern.finditer(content[:2000]):
            value = match.group(1)
            unit = match.group(2).lower()
            seen.setdefault(unit, {}).setdefault(value, []).append(
                {"title": source.get("title"), "url": source.get("url")}
            )
    conflicts = []
    for unit, values in seen.items():
        if len(values) > 1:
            conflicts.append({
                "unit": unit,
                "values": [
                    {"value": v, "sources": src_list[:2]}
                    for v, src_list in values.items()
                ],
            })
    return conflicts


def build_learning_pack(query: str, response: str, sources: List[Dict[str, Any]]) -> str:
    """Build a structured learning pack (summary + quiz + sources) for a query."""
    clean_response = response.split("### Sources", 1)[0].strip()
    sentences = re.split(r"(?<=[.!?])\s+", clean_response)
    summary = " ".join(sentences[:3]).strip()

    keywords = extract_keywords(clean_response, max_terms=8)
    terms_section = "\n".join([
        f"- **{term.title()}**: {term} is discussed in the research findings."
        for term in keywords
    ])

    quiz_terms = keywords[:3] if keywords else ["this topic"]
    quiz_questions = "\n".join([
        f"1. What is {quiz_terms[0].title()} and why does it matter in this context?",
        (
            f"2. How would you apply {quiz_terms[1].title()} in a real-world scenario?"
            if len(quiz_terms) > 1
            else "2. What is the most important takeaway from the research?"
        ),
        (
            f"3. What assumptions or limitations surround {quiz_terms[2].title()}?"
            if len(quiz_terms) > 2
            else "3. Which source would you trust most and why?"
        ),
    ])

    source_list = "\n".join([
        f"- [{s.get('title', 'Source')}]({s.get('url', '#')})"
        for s in sources[:5]
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


# ── File helpers ──────────────────────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file using pdftotext (poppler-utils)."""
    if not shutil.which("pdftotext"):
        return ""
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "upload.pdf"
        txt_path = Path(temp_dir) / "upload.txt"
        pdf_path.write_bytes(file_bytes)
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not txt_path.exists():
            return ""
        return txt_path.read_text(errors="ignore")


# ── Network helpers ───────────────────────────────────────────────────────────

async def check_internet() -> Dict[str, Any]:
    """Check internet connectivity via curl."""
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["curl", "-I", "-s", "--max-time", "10", "https://duckduckgo.com"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        first_line = (result.stdout or result.stderr).split("\n")[0].strip()
        online = result.returncode == 0 and any(
            code in first_line for code in ("200", "301", "302")
        )
        return {"online": online, "details": first_line}
    except Exception as e:
        logger.warning(f"Internet check failed: {e}")
        return {"online": False, "details": str(e)}

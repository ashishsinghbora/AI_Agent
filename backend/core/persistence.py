"""Persistent Session Storage: SQLite + File Backend"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ResearchSession:
    """In-memory session data model"""
    session_id: str
    query: str
    created_at: str
    updated_at: str
    status: str  # "in_progress", "completed", "failed"
    output_mode: str  # "quick", "full", "paper"
    findings_count: int = 0
    sources: List[Dict[str, Any]] = None
    thinking: str = ""
    response: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}


class SessionRepository:
    """SQLite backend for session persistence"""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS research_sessions (
        session_id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        status TEXT NOT NULL,
        output_mode TEXT NOT NULL,
        findings_count INTEGER DEFAULT 0,
        sources_json TEXT DEFAULT '[]',
        metadata_json TEXT DEFAULT '{}',
        created_ip TEXT,
        device_name TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_created_at ON research_sessions(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_status ON research_sessions(status);
    """

    def __init__(self, db_path: Path):
        """Initialize SQLite database"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for stmt in self.SCHEMA.split(';'):
                    if stmt.strip():
                        conn.execute(stmt)
                conn.commit()
                logger.info(f"SessionRepository initialized: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database init error: {e}")
            raise

    def create_session(self, session: ResearchSession) -> bool:
        """Create new session record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO research_sessions 
                    (session_id, query, created_at, updated_at, status, output_mode, findings_count, sources_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.session_id,
                        session.query,
                        session.created_at,
                        session.updated_at,
                        session.status,
                        session.output_mode,
                        session.findings_count,
                        json.dumps(session.sources or []),
                        json.dumps(session.metadata or {})
                    )
                )
                conn.commit()
                logger.info(f"Session created: {session.session_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Create session error: {e}")
            return False

    def update_session(self, session: ResearchSession) -> bool:
        """Update existing session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE research_sessions
                    SET query = ?, updated_at = ?, status = ?, output_mode = ?,
                        findings_count = ?, sources_json = ?, metadata_json = ?
                    WHERE session_id = ?
                    """,
                    (
                        session.query,
                        session.updated_at,
                        session.status,
                        session.output_mode,
                        session.findings_count,
                        json.dumps(session.sources or []),
                        json.dumps(session.metadata or {}),
                        session.session_id
                    )
                )
                conn.commit()
                logger.info(f"Session updated: {session.session_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Update session error: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Retrieve session by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM research_sessions WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                return ResearchSession(
                    session_id=row["session_id"],
                    query=row["query"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    status=row["status"],
                    output_mode=row["output_mode"],
                    findings_count=row["findings_count"],
                    sources=json.loads(row["sources_json"] or "[]"),
                    metadata=json.loads(row["metadata_json"] or "{}")
                )
        except sqlite3.Error as e:
            logger.error(f"Get session error: {e}")
            return None

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[ResearchSession]:
        """List all sessions (paginated)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM research_sessions
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset)
                )
                sessions = []
                for row in cursor:
                    sessions.append(ResearchSession(
                        session_id=row["session_id"],
                        query=row["query"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        status=row["status"],
                        output_mode=row["output_mode"],
                        findings_count=row["findings_count"],
                        sources=json.loads(row["sources_json"] or "[]"),
                        metadata=json.loads(row["metadata_json"] or "{}")
                    ))
                return sessions
        except sqlite3.Error as e:
            logger.error(f"List sessions error: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM research_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                logger.info(f"Session deleted: {session_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Delete session error: {e}")
            return False

    def search_sessions(self, query: str, limit: int = 20) -> List[ResearchSession]:
        """Search sessions by query text"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM research_sessions
                    WHERE query LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", limit)
                )
                sessions = []
                for row in cursor:
                    sessions.append(ResearchSession(
                        session_id=row["session_id"],
                        query=row["query"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        status=row["status"],
                        output_mode=row["output_mode"],
                        findings_count=row["findings_count"],
                        sources=json.loads(row["sources_json"] or "[]"),
                        metadata=json.loads(row["metadata_json"] or "{}")
                    ))
                return sessions
        except sqlite3.Error as e:
            logger.error(f"Search sessions error: {e}")
            return []


class FileBackend:
    """JSON file-based backup storage (fallback to SQLite)"""

    def __init__(self, base_path: Path):
        """Args: base_path (research_notes directory)"""
        self.base_path = base_path
        self.sessions_dir = base_path / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    async def save_session_snapshot(self, session: ResearchSession) -> bool:
        """Save session to JSON file (async)"""
        try:
            file_path = self.sessions_dir / f"{session.session_id}.json"
            data = asdict(session)
            data["sources"] = session.sources or []
            data["metadata"] = session.metadata or {}
            
            # Use sync write for now (can upgrade to aiofiles later)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Session snapshot saved: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Save snapshot error: {e}")
            return False

    async def load_session_snapshot(self, session_id: str) -> Optional[ResearchSession]:
        """Load session from JSON file (async)"""
        try:
            file_path = self.sessions_dir / f"{session_id}.json"
            if not file_path.exists():
                return None
                
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return ResearchSession(**data)
        except Exception as e:
            logger.error(f"Load snapshot error: {e}")
            return None

    async def list_snapshots(self) -> List[str]:
        """List all saved session snapshots"""
        try:
            return [f.stem for f in self.sessions_dir.glob("*.json")]
        except Exception as e:
            logger.error(f"List snapshots error: {e}")
            return []

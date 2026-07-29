"""Persist practice sessions and a simple local profile."""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from uuid import UUID, uuid4

from fretflow.core.errors import PersistenceError
from fretflow.core.models import Session
from fretflow.core.paths import library_db_path
from fretflow.library.db import connect

logger = logging.getLogger("fretflow.profile.repository")

SESSIONS_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    song_id TEXT NOT NULL,
    started_at REAL NOT NULL,
    duration_seconds REAL NOT NULL DEFAULT 0,
    notes_hit INTEGER NOT NULL DEFAULT 0,
    notes_missed INTEGER NOT NULL DEFAULT 0,
    notes_expected INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,
    max_combo INTEGER NOT NULL DEFAULT 0,
    tempo_factor REAL NOT NULL DEFAULT 1.0,
    section_start_seconds REAL,
    section_end_seconds REAL
);

CREATE INDEX IF NOT EXISTS idx_sessions_song ON sessions(song_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);

CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0
);
"""


def ensure_session_tables(db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SESSIONS_SQL)
        conn.commit()


class SessionRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path
        ensure_session_tables(db_path)

    def save(self, session: Session) -> None:
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO sessions (
                        id, song_id, started_at, duration_seconds,
                        notes_hit, notes_missed, notes_expected,
                        score, max_combo, tempo_factor,
                        section_start_seconds, section_end_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        duration_seconds = excluded.duration_seconds,
                        notes_hit = excluded.notes_hit,
                        notes_missed = excluded.notes_missed,
                        notes_expected = excluded.notes_expected,
                        score = excluded.score,
                        max_combo = excluded.max_combo
                    """,
                    (
                        str(session.id),
                        str(session.song_id),
                        session.started_at,
                        session.duration_seconds,
                        session.notes_hit,
                        session.notes_missed,
                        session.notes_expected,
                        session.score,
                        session.max_combo,
                        session.tempo_factor,
                        session.section_start_seconds,
                        session.section_end_seconds,
                    ),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Cannot save session: {exc}") from exc
        logger.info("Saved session %s (score=%d)", session.id, session.score)

    def list_for_song(self, song_id: UUID | str, limit: int = 20) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM sessions WHERE song_id = ?
                ORDER BY started_at DESC LIMIT ?
                """,
                (str(song_id), limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_recent(self, limit: int = 20) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]


class ProfileRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path
        ensure_session_tables(db_path)

    def ensure_default(self, name: str = "Joueur") -> dict:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM profiles WHERE is_active = 1 LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)
            pid = str(uuid4())
            conn.execute(
                "INSERT INTO profiles (id, name, created_at, is_active) VALUES (?, ?, ?, 1)",
                (pid, name, time.time()),
            )
            conn.commit()
            return {"id": pid, "name": name, "is_active": 1}

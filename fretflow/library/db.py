"""SQLite connection helpers."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from fretflow.core.errors import PersistenceError
from fretflow.core.paths import library_db_path
from fretflow.library.migrations import CURRENT_VERSION, apply_migrations
from fretflow.library.schema import SCHEMA_SQL, SCHEMA_VERSION

logger = logging.getLogger("fretflow.library.db")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open (and initialise) the library database."""
    path = db_path or library_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(conn)
        return conn
    except sqlite3.Error as exc:
        raise PersistenceError(f"Cannot open library database {path}: {exc}") from exc


def _ensure_schema(conn: sqlite3.Connection) -> None:
    version = apply_migrations(conn)
    # Keep legacy SCHEMA_SQL as safety net for songs table if migration 1 was skipped
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='songs'"
    )
    if cur.fetchone() is None:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    logger.debug("Library schema version: %d (target %d)", version, CURRENT_VERSION)

"""SQLite connection helpers."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from fretflow.core.errors import PersistenceError
from fretflow.core.paths import library_db_path
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
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cur.fetchone() is None:
        conn.executescript(SCHEMA_SQL)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
        logger.info("Initialised library schema v%d", SCHEMA_VERSION)
        return

    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    current = int(row["version"]) if row else 0
    if current < SCHEMA_VERSION:
        # Future migrations go here
        conn.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))
        conn.commit()
        logger.info("Migrated library schema %d → %d", current, SCHEMA_VERSION)

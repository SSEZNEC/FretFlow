"""Versioned SQLite schema migrations."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable

logger = logging.getLogger("fretflow.library.migrations")

MigrationFn = Callable[[sqlite3.Connection], None]

# Each migration upgrades FROM version N-1 TO version N
MIGRATIONS: dict[int, MigrationFn] = {}


def migration(version: int) -> Callable[[MigrationFn], MigrationFn]:
    def decorator(fn: MigrationFn) -> MigrationFn:
        MIGRATIONS[version] = fn
        return fn
    return decorator


@migration(1)
def _v1_base(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS songs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        artist TEXT NOT NULL DEFAULT '',
        tempo_bpm REAL NOT NULL DEFAULT 120.0,
        duration_seconds REAL NOT NULL DEFAULT 0.0,
        time_signature TEXT NOT NULL DEFAULT '4/4',
        source_path TEXT,
        file_hash TEXT,
        track_count INTEGER NOT NULL DEFAULT 0,
        imported_at REAL NOT NULL,
        last_practiced_at REAL,
        practice_count INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
    CREATE TABLE IF NOT EXISTS tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        midi_channel INTEGER NOT NULL DEFAULT 0,
        is_guitar INTEGER NOT NULL DEFAULT 1,
        note_count INTEGER NOT NULL DEFAULT 0,
        UNIQUE(song_id, name)
    );
    """)


@migration(2)
def _v2_sessions_skills(conn: sqlite3.Connection) -> None:
    conn.executescript("""
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
    CREATE TABLE IF NOT EXISTS skill_profiles (
        id TEXT PRIMARY KEY,
        levels_json TEXT NOT NULL DEFAULT '{}',
        updated_at REAL NOT NULL
    );
    """)


CURRENT_VERSION = max(MIGRATIONS.keys()) if MIGRATIONS else 0


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply pending migrations. Returns the resulting schema version."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        current = 0
        conn.execute("INSERT INTO schema_version (version) VALUES (0)")
    else:
        current = int(row[0] if not hasattr(row, "keys") else row["version"])

    for version in sorted(MIGRATIONS.keys()):
        if version <= current:
            continue
        logger.info("Applying migration v%d", version)
        MIGRATIONS[version](conn)
        conn.execute("UPDATE schema_version SET version = ?", (version,))
        current = version

    conn.commit()
    return current

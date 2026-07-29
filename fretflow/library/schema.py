"""SQLite schema for the song library (versioned)."""

from __future__ import annotations

SCHEMA_VERSION = 1

SCHEMA_SQL = """
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
CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist);
CREATE INDEX IF NOT EXISTS idx_songs_path ON songs(source_path);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    midi_channel INTEGER NOT NULL DEFAULT 0,
    is_guitar INTEGER NOT NULL DEFAULT 1,
    note_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(song_id, name)
);
"""

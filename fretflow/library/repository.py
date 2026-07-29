"""Song library repository (CRUD on SQLite)."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from uuid import UUID

from fretflow.core.errors import PersistenceError
from fretflow.core.models import Song
from fretflow.library.db import connect

logger = logging.getLogger("fretflow.library.repository")


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class SongRepository:
    """Persist and query song metadata (not the full timeline)."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def upsert_song(self, song: Song) -> None:
        """Insert or update a song and its track summaries."""
        if song.source_path is None:
            file_hash = None
            path_str = None
        else:
            path_str = str(song.source_path)
            try:
                file_hash = _file_hash(song.source_path)
            except OSError:
                file_hash = None

        now = time.time()
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO songs (
                        id, title, artist, tempo_bpm, duration_seconds,
                        time_signature, source_path, file_hash, track_count,
                        imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        artist = excluded.artist,
                        tempo_bpm = excluded.tempo_bpm,
                        duration_seconds = excluded.duration_seconds,
                        time_signature = excluded.time_signature,
                        source_path = excluded.source_path,
                        file_hash = excluded.file_hash,
                        track_count = excluded.track_count
                    """,
                    (
                        str(song.id),
                        song.title,
                        song.artist,
                        song.tempo_bpm,
                        song.duration_seconds,
                        song.time_signature,
                        path_str,
                        file_hash,
                        len(song.tracks),
                        now,
                    ),
                )
                conn.execute("DELETE FROM tracks WHERE song_id = ?", (str(song.id),))
                for track in song.tracks:
                    conn.execute(
                        """
                        INSERT INTO tracks (song_id, name, midi_channel, is_guitar, note_count)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            str(song.id),
                            track.name,
                            track.midi_channel,
                            1 if track.is_guitar else 0,
                            len(track.notes),
                        ),
                    )
                conn.commit()
        except Exception as exc:
            raise PersistenceError(f"Failed to upsert song {song.title}: {exc}") from exc

        logger.info("Upserted song '%s' (%s)", song.title, song.id)

    def find_by_path(self, path: Path) -> dict | None:
        """Return song row for a given source path, or None."""
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM songs WHERE source_path = ?", (str(path.resolve()),)
            ).fetchone()
            return dict(row) if row else None

    def find_by_hash(self, file_hash: str) -> dict | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM songs WHERE file_hash = ?", (file_hash,)
            ).fetchone()
            return dict(row) if row else None

    def list_songs(self) -> list[dict]:
        """Return all songs ordered by title."""
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM songs ORDER BY title COLLATE NOCASE"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_song(self, song_id: UUID | str) -> dict | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM songs WHERE id = ?", (str(song_id),)
            ).fetchone()
            return dict(row) if row else None

    def get_tracks(self, song_id: UUID | str) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM tracks WHERE song_id = ? ORDER BY id",
                (str(song_id),),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_song(self, song_id: UUID | str) -> None:
        with connect(self._db_path) as conn:
            conn.execute("DELETE FROM songs WHERE id = ?", (str(song_id),))
            conn.commit()

    def count(self) -> int:
        with connect(self._db_path) as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM songs").fetchone()
            return int(row["n"])

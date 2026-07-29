"""Tests for session persistence."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fretflow.core.models import Session
from fretflow.profile.repository import ProfileRepository, SessionRepository


def test_save_and_list(tmp_path: Path) -> None:
    db = tmp_path / "lib.db"
    repo = SessionRepository(db_path=db)
    song_id = uuid4()
    session = Session(
        song_id=song_id,
        started_at=1_700_000_000.0,
        duration_seconds=42.0,
        notes_hit=10,
        notes_missed=2,
        notes_expected=12,
        score=900,
        max_combo=5,
        tempo_factor=0.8,
    )
    repo.save(session)
    rows = repo.list_for_song(song_id)
    assert len(rows) == 1
    assert rows[0]["score"] == 900
    assert rows[0]["notes_hit"] == 10


def test_default_profile(tmp_path: Path) -> None:
    db = tmp_path / "lib.db"
    profile = ProfileRepository(db_path=db).ensure_default("Testeur")
    assert profile["name"] == "Testeur"
    again = ProfileRepository(db_path=db).ensure_default()
    assert again["id"] == profile["id"]

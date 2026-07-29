"""Tests for SQLite library repository and scanner."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import mido
import pytest

from fretflow.core.models import Note, Song, Track
from fretflow.library.repository import SongRepository
from fretflow.library.scanner import LibraryScanner


def _midi(path: Path) -> None:
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    track.append(mido.Message("note_on", note=60, velocity=80, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=480))
    mid.save(str(path))


def test_upsert_and_list(tmp_path: Path) -> None:
    db = tmp_path / "lib.db"
    repo = SongRepository(db_path=db)

    song = Song(
        title="Fixture Riff",
        artist="Test",
        tempo_bpm=110.0,
        tracks=[
            Track(
                name="Lead",
                measures=[],
            )
        ],
        duration_seconds=4.0,
    )
    # attach a note via a measure-less track for simplicity
    song.tracks[0].measures = []
    repo.upsert_song(song)

    assert repo.count() == 1
    rows = repo.list_songs()
    assert rows[0]["title"] == "Fixture Riff"
    assert rows[0]["artist"] == "Test"
    assert float(rows[0]["tempo_bpm"]) == 110.0

    tracks = repo.get_tracks(song.id)
    assert len(tracks) == 1
    assert tracks[0]["name"] == "Lead"


def test_scanner_imports_midi(tmp_path: Path) -> None:
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()
    midi_path = songs_dir / "riff.mid"
    _midi(midi_path)

    db = tmp_path / "lib.db"
    repo = SongRepository(db_path=db)
    scanner = LibraryScanner(repository=repo)
    result = scanner.scan([songs_dir])

    assert result.imported == 1
    assert result.failed == 0
    assert repo.count() == 1

    # Second scan should skip unchanged file
    result2 = scanner.scan([songs_dir])
    assert result2.skipped == 1
    assert result2.imported == 0
    assert repo.count() == 1


def test_scanner_force_reimport(tmp_path: Path) -> None:
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()
    _midi(songs_dir / "a.mid")

    db = tmp_path / "lib.db"
    repo = SongRepository(db_path=db)
    scanner = LibraryScanner(repository=repo)
    scanner.scan([songs_dir])
    result = scanner.scan([songs_dir], force=True)
    assert result.imported == 1
    assert result.skipped == 0

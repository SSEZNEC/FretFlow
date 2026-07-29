"""Unit tests for core domain models."""

from __future__ import annotations

import pytest

from fretflow.core.models import Measure, Note, Session, Song, Technique, Track
from fretflow.core.time_units import ms_to_seconds, seconds_to_ms


def test_note_valid() -> None:
    note = Note(start_seconds=1.0, duration_seconds=0.5, midi_pitch=64)
    assert note.midi_pitch == 64
    assert note.technique is Technique.NONE


def test_note_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration_seconds"):
        Note(start_seconds=0.0, duration_seconds=-0.1, midi_pitch=60)


def test_note_rejects_invalid_pitch() -> None:
    with pytest.raises(ValueError, match="midi_pitch"):
        Note(start_seconds=0.0, duration_seconds=0.1, midi_pitch=128)


def test_track_flattens_notes() -> None:
    n1 = Note(0.0, 0.5, 60)
    n2 = Note(1.0, 0.5, 62)
    measure = Measure(index=0, start_seconds=0.0, duration_seconds=2.0, notes=[n1, n2])
    track = Track(name="Lead", measures=[measure])
    assert track.notes == [n1, n2]


def test_song_primary_track_prefers_guitar() -> None:
    drums = Track(name="Drums", is_guitar=False)
    guitar = Track(name="Guitar", is_guitar=True)
    song = Song(title="Test", tracks=[drums, guitar])
    assert song.primary_track() is guitar


def test_song_primary_track_fallback() -> None:
    bass = Track(name="Bass", is_guitar=False)
    song = Song(title="Test", tracks=[bass])
    assert song.primary_track() is bass


def test_session_accuracy() -> None:
    session = Session(song_id=Song(title="x").id, started_at=0.0, notes_hit=8, notes_missed=2)
    assert session.accuracy == pytest.approx(0.8)


def test_session_accuracy_empty() -> None:
    session = Session(song_id=Song(title="x").id, started_at=0.0)
    assert session.accuracy == 0.0


def test_time_unit_roundtrip() -> None:
    assert seconds_to_ms(1.5) == 1500.0
    assert ms_to_seconds(1500.0) == 1.5

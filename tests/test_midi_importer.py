"""Tests for the MIDI importer using synthetic fixtures."""

from __future__ import annotations

from pathlib import Path

import mido
import pytest

from fretflow.core.errors import ImportError as FretFlowImportError
from fretflow.importers.midi import MidiImporter


def _write_simple_midi(path: Path, *, tempo_bpm: float = 120.0) -> None:
    """Write a minimal Type-1 MIDI with a few notes on channel 0."""
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    tempo = mido.bpm2tempo(tempo_bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    track.append(mido.MetaMessage("track_name", name="Test Lead", time=0))

    # C4 quarter, E4 quarter, G4 half
    track.append(mido.Message("note_on", note=60, velocity=80, channel=0, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    track.append(mido.Message("note_on", note=64, velocity=80, channel=0, time=0))
    track.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=480))
    track.append(mido.Message("note_on", note=67, velocity=90, channel=0, time=0))
    track.append(mido.Message("note_off", note=67, velocity=0, channel=0, time=960))

    mid.save(str(path))


def test_can_import() -> None:
    importer = MidiImporter()
    assert importer.can_import(Path("song.mid"))
    assert importer.can_import(Path("song.MIDI"))
    assert not importer.can_import(Path("song.gp5"))


def test_import_simple_midi(tmp_path: Path) -> None:
    path = tmp_path / "simple.mid"
    _write_simple_midi(path, tempo_bpm=100.0)

    song = MidiImporter().import_song(path)
    assert song.title  # at least stem or track name
    assert abs(song.tempo_bpm - 100.0) < 0.1
    assert len(song.tracks) >= 1
    notes = song.primary_track().notes  # type: ignore[union-attr]
    assert len(notes) == 3
    assert notes[0].midi_pitch == 60
    assert notes[1].midi_pitch == 64
    assert notes[2].midi_pitch == 67
    assert song.duration_seconds > 0


def test_import_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FretFlowImportError, match="not found"):
        MidiImporter().import_song(tmp_path / "absent.mid")


def test_import_song_dispatch(tmp_path: Path) -> None:
    from fretflow.importers import import_song

    path = tmp_path / "dispatch.mid"
    _write_simple_midi(path)
    song = import_song(path)
    assert len(song.tracks) >= 1

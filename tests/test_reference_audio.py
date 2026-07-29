"""Tests for reference audio, ear training and call-response."""

from __future__ import annotations

import numpy as np
import pytest

from fretflow.audio.reference_audio import ReferenceAudioEngine, ReferenceMode
from fretflow.audio.sample_player import NullSink
from fretflow.audio.sound_bank import SoundBank, Timbre, synthesize_note
from fretflow.coach.ear_training import EarExerciseKind, EarTrainingSession
from fretflow.coach.phrase_generator import CallResponseSession, PhraseGenerator
from fretflow.core.models import Note
from fretflow.practice.chord_library import list_open_chords, lookup_chord


def test_synthesize_note_shape() -> None:
    wave = synthesize_note(60, duration=0.2, sample_rate=22050)
    assert wave.dtype == np.float32
    assert wave.size > 100
    assert float(np.max(np.abs(wave))) <= 1.0


def test_sound_bank_cache() -> None:
    bank = SoundBank(timbre=Timbre.CLEAN, sample_rate=22050)
    a = bank.get(60, 0.3)
    b = bank.get(60, 0.3)
    assert a is b  # cached


def test_reference_plays_note() -> None:
    sink = NullSink()
    eng = ReferenceAudioEngine(mode=ReferenceMode.NOTE, sink=sink)
    note = Note(0.0, 0.3, 64, string=1, fret=0)
    eng.on_note_approaching(note)
    eng.on_note_approaching(note)  # dedup
    assert sink.play_count == 1


def test_reference_off() -> None:
    sink = NullSink()
    eng = ReferenceAudioEngine(mode=ReferenceMode.OFF, sink=sink)
    eng.on_note_approaching(Note(0.0, 0.2, 60))
    assert sink.play_count == 0


def test_reference_silent_on_error() -> None:
    sink = NullSink()
    eng = ReferenceAudioEngine(mode=ReferenceMode.SILENT_ON_ERROR, sink=sink)
    eng.on_note_approaching(Note(0.0, 0.2, 60))
    assert sink.play_count == 0
    eng.on_miss(60)
    assert sink.play_count == 1


def test_ear_training_session() -> None:
    sink = NullSink()
    eng = ReferenceAudioEngine(sink=sink)
    session = EarTrainingSession(engine=eng)
    ch = session.next_challenge(EarExerciseKind.SINGLE_NOTE)
    session.play_prompt()
    assert sink.play_count >= 1
    ok = session.submit(ch.primary_midi)
    assert ok.correct
    bad = session.submit(ch.primary_midi + 1)
    # after submit, still counts
    assert session.accuracy > 0


def test_phrase_generator() -> None:
    phrase = PhraseGenerator().scale_fragment(length=4)
    assert len(phrase.notes) == 4
    assert all(n.string is not None for n in phrase.notes)


def test_call_response_score() -> None:
    session = CallResponseSession()
    phrase = session.next_phrase(length=3)
    played = [n.midi_pitch for n in phrase.notes]
    result = session.score_response(played)
    assert result.accuracy == pytest.approx(1.0)


def test_chord_library() -> None:
    assert "Em" in list_open_chords()
    shape = lookup_chord("G")
    assert shape is not None
    assert len(shape.positions) >= 3

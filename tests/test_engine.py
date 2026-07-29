"""Tests for game clock, judgment and session runner."""

from __future__ import annotations

import time

import pytest

from fretflow.core.config import JudgmentWindows
from fretflow.core.models import Measure, Note, Song, Track
from fretflow.engine.clock import ClockState, GameClock
from fretflow.engine.events import PlayedNoteEvent
from fretflow.engine.judgment import Judgment, judge_note
from fretflow.engine.session_runner import SessionRunner
from fretflow.practice.settings import PracticeSettings


def test_judge_perfect() -> None:
    r = judge_note(1.0, 1.0)
    assert r.judgment is Judgment.PERFECT
    assert r.offset_ms == pytest.approx(0.0)


def test_judge_great() -> None:
    # 40 ms late → Great (default window 60)
    r = judge_note(1.0, 1.04)
    assert r.judgment is Judgment.GREAT


def test_judge_miss() -> None:
    r = judge_note(1.0, 1.2)
    assert r.judgment is Judgment.MISS


def test_clock_seek_and_tempo() -> None:
    clock = GameClock(duration_seconds=10.0, tempo_factor=1.0)
    clock.seek(3.0)
    assert clock.current_time() == pytest.approx(3.0)
    clock.set_tempo_factor(0.5)
    assert clock.tempo_factor == 0.5


def test_clock_runs_forward() -> None:
    clock = GameClock(duration_seconds=10.0, tempo_factor=1.0)
    clock.start()
    time.sleep(0.05)
    t = clock.current_time()
    assert t > 0.02
    clock.pause()
    t2 = clock.current_time()
    time.sleep(0.03)
    assert clock.current_time() == pytest.approx(t2, abs=0.01)


def _demo_song() -> Song:
    notes = [
        Note(start_seconds=0.0, duration_seconds=0.3, midi_pitch=60),
        Note(start_seconds=0.5, duration_seconds=0.3, midi_pitch=64),
        Note(start_seconds=1.0, duration_seconds=0.3, midi_pitch=67),
    ]
    measure = Measure(index=0, start_seconds=0.0, duration_seconds=2.0, notes=notes)
    track = Track(name="Lead", measures=[measure])
    return Song(title="Test", tempo_bpm=120.0, tracks=[track], duration_seconds=2.0)


def test_session_perfect_hits() -> None:
    song = _demo_song()
    settings = PracticeSettings(song_id=song.id, tempo_factor=1.0)
    runner = SessionRunner(song=song, settings=settings)
    runner.start()

    for note in song.tracks[0].notes:
        runner.clock.seek(note.start_seconds)
        hit = runner.handle_played_note(
            PlayedNoteEvent(midi_pitch=note.midi_pitch, time_seconds=note.start_seconds)
        )
        assert hit is not None
        assert hit.judgment is Judgment.PERFECT

    report = runner.build_report()
    assert report.notes_hit == 3
    assert report.notes_missed == 0
    assert report.accuracy == pytest.approx(1.0)
    assert report.max_combo == 3


def test_session_auto_miss() -> None:
    song = _demo_song()
    settings = PracticeSettings(song_id=song.id)
    # Tight windows so we can jump past notes
    windows = JudgmentWindows(perfect_ms=10, great_ms=20, good_ms=30)
    runner = SessionRunner(song=song, settings=settings, windows=windows)
    runner.start()
    runner.clock.seek(2.0)  # past everything
    misses = runner.tick()
    assert len(misses) == 3
    report = runner.build_report()
    assert report.notes_missed == 3
    assert report.notes_hit == 0


def test_section_filter() -> None:
    song = _demo_song()
    settings = PracticeSettings(
        song_id=song.id,
        section_start_seconds=0.4,
        section_end_seconds=1.5,
    )
    runner = SessionRunner(song=song, settings=settings)
    assert runner.expected_count == 2  # notes at 0.5 and 1.0

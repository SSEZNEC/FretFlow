"""Integration tests for coach service and report builder."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from fretflow.coach import CoachService, SkillId
from fretflow.core.models import Measure, Note, Song, Track
from fretflow.engine import PlayedNoteEvent, SessionRunner
from fretflow.practice import PracticeSettings
from fretflow.practice.report_builder import report_from_runner
from fretflow.profile.skills_store import SkillStore


def _song() -> Song:
    notes = [
        Note(start_seconds=i * 0.5, duration_seconds=0.3, midi_pitch=60 + (i % 5))
        for i in range(10)
    ]
    return Song(
        title="Coach Test",
        tracks=[Track(name="T", measures=[Measure(0, 0.0, 5.0, notes=notes)])],
        duration_seconds=5.0,
    )


def test_report_from_runner_perfect() -> None:
    song = _song()
    runner = SessionRunner(song=song, settings=PracticeSettings(song_id=song.id))
    runner.start()
    for note in song.tracks[0].notes:
        runner.clock.seek(note.start_seconds)
        runner.handle_played_note(
            PlayedNoteEvent(midi_pitch=note.midi_pitch, time_seconds=note.start_seconds)
        )
    report = report_from_runner(runner)
    assert report.notes_hit == 10
    assert report.accuracy == pytest.approx(1.0)
    assert len(report.sections) >= 1


def test_coach_service_persists_skills(tmp_path: Path) -> None:
    song = _song()
    runner = SessionRunner(song=song, settings=PracticeSettings(song_id=song.id))
    runner.start()
    # Play only first 3 notes perfectly, skip the rest (will miss via tick)
    for note in song.tracks[0].notes[:3]:
        runner.clock.seek(note.start_seconds)
        runner.handle_played_note(
            PlayedNoteEvent(midi_pitch=note.midi_pitch, time_seconds=note.start_seconds)
        )
    runner.clock.seek(5.0)
    runner.tick()

    store = SkillStore(db_path=tmp_path / "lib.db")
    service = CoachService(skill_store=store)
    result = service.analyse_runner(runner)

    assert result.report.notes_expected == 10
    assert len(result.recommendations) >= 1
    assert result.plan.exercise_count >= 1

    reloaded = store.load()
    assert reloaded.get(SkillId.PITCH_ACCURACY).sample_count >= 1

    text = service.format_result(result)
    assert "Recommandations" in text or "recommandation" in text.lower() or "Precision" in text


def test_goals_progress() -> None:
    from fretflow.coach.goals import GoalTracker

    tracker = GoalTracker()
    tracker.record_session(duration_seconds=600, accuracy=0.9)  # 10 min
    assert any(g.current_value >= 1 for g in tracker.daily)

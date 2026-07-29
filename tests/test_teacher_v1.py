"""Virtual guitar teacher — tips, plans, dialogue, feedback."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fretflow.audio.feedback import PitchFeedback, compare_pitch
from fretflow.audio.types import PitchEstimate
from fretflow.coach.dialogue import build_dialogue
from fretflow.coach.teacher_tips import TeacherTipEngine, TipKind
from fretflow.coach.training_plan import BlockKind, TrainingPlanBuilder
from fretflow.core.models import Note, Technique
from fretflow.practice.fretboard import FretMarker, FretPosition
from fretflow.practice.session_report import NoteOutcome, SessionReport, build_sections_from_outcomes


def test_tips_prepare_barre() -> None:
    engine = TeacherTipEngine()
    positions = [
        FretPosition(string=s, fret=5, finger=1, marker=FretMarker.CURRENT)
        for s in range(1, 6)
    ]
    tips = engine.tips_at(0.0, [], positions)
    assert any(t.kind is TipKind.PREPARE for t in tips)


def test_tips_technique_upcoming() -> None:
    engine = TeacherTipEngine()
    notes = [Note(1.0, 0.3, 64, technique=Technique.BEND)]
    tips = engine.tips_at(0.0, notes, [])
    assert any("bend" in t.message.lower() for t in tips)


def test_tips_encouragement() -> None:
    engine = TeacherTipEngine()
    tips = engine.tips_at(0.0, [], [], last_hit=True, last_offset_ms=5.0)
    assert any(t.kind is TipKind.ENCOURAGE for t in tips)


def test_training_plan_structure() -> None:
    plan = TrainingPlanBuilder().build(total_minutes=45, song_title="Demo")
    assert abs(plan.total_minutes - 45) < 1.0
    kinds = [b.kind for b in plan.blocks]
    assert BlockKind.WARMUP in kinds
    assert BlockKind.SONG in kinds
    assert BlockKind.COOLDOWN in kinds
    assert plan.to_exercise_plan().exercise_count >= 1


def test_dialogue_positive() -> None:
    outcomes = [
        NoteOutcome(i * 0.5, 60, True, 5.0) for i in range(10)
    ]
    report = SessionReport(
        session_id=uuid4(),
        song_id=uuid4(),
        outcomes=outcomes,
        sections=build_sections_from_outcomes(outcomes),
        duration_seconds=300,
    )
    lines = build_dialogue(report, [])
    assert len(lines) >= 2
    assert any("progress" in l.lower() or "solide" in l.lower() or "Bonne" in l for l in lines)


def test_pitch_feedback_correct() -> None:
    est = PitchEstimate(440.0, 69.0, 0.9, 0.0)
    r = compare_pitch(est, 69)
    assert r.kind is PitchFeedback.CORRECT


def test_pitch_feedback_sharp() -> None:
    est = PitchEstimate(466.0, 70.5, 0.9, 0.0)  # ~150 cents sharp of 69
    r = compare_pitch(est, 69)
    assert r.kind is PitchFeedback.SHARP

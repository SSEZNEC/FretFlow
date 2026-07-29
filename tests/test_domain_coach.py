"""Domain tests: practice exercises + coach reasoning."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fretflow.coach import (
    RecommendationEngine,
    SkillId,
    SkillProfile,
    detect_weaknesses,
)
from fretflow.coach.weakness_detector import WeaknessKind
from fretflow.practice import (
    Exercise,
    ExerciseKind,
    ExercisePlan,
    NoteOutcome,
    SessionReport,
    build_sections_from_outcomes,
)


def _report_with_hard_section() -> SessionReport:
    song_id = uuid4()
    session_id = uuid4()
    outcomes = []
    # 0-4s: all hits
    for i in range(8):
        outcomes.append(
            NoteOutcome(expected_seconds=i * 0.5, midi_pitch=60, hit=True, offset_ms=5.0)
        )
    # 4-8s: mostly misses
    for i in range(8):
        outcomes.append(
            NoteOutcome(
                expected_seconds=4.0 + i * 0.5,
                midi_pitch=62,
                hit=(i % 4 == 0),
                offset_ms=10.0 if i % 4 == 0 else None,
            )
        )
    sections = build_sections_from_outcomes(outcomes, window_seconds=4.0)
    return SessionReport(
        session_id=session_id,
        song_id=song_id,
        outcomes=outcomes,
        sections=sections,
        tempo_factor=1.0,
        score=200,
    )


def test_exercise_validation() -> None:
    with pytest.raises(ValueError):
        Exercise(title="x", kind=ExerciseKind.CUSTOM, tempo_factor=0.1)
    with pytest.raises(ValueError):
        Exercise(
            title="x",
            kind=ExerciseKind.SECTION_LOOP,
            section_start_seconds=5.0,
            section_end_seconds=2.0,
        )


def test_exercise_plan_progress() -> None:
    plan = ExercisePlan(title="Test")
    a = Exercise(title="A", kind=ExerciseKind.CUSTOM)
    b = Exercise(title="B", kind=ExerciseKind.CUSTOM)
    plan.add(a)
    plan.add(b)
    assert plan.next_exercise(set()) is a
    assert plan.progress_ratio({a.id}) == pytest.approx(0.5)
    assert plan.next_exercise({a.id}) is b
    assert plan.next_exercise({a.id, b.id}) is None


def test_build_sections() -> None:
    outcomes = [
        NoteOutcome(0.5, 60, True, 0.0),
        NoteOutcome(1.0, 62, False, None),
        NoteOutcome(5.0, 64, True, 20.0),
    ]
    sections = build_sections_from_outcomes(outcomes, window_seconds=4.0)
    assert len(sections) == 2
    assert sections[0].notes_expected == 2
    assert sections[1].notes_hit == 1


def test_detect_hard_section() -> None:
    report = _report_with_hard_section()
    weaknesses = detect_weaknesses(report)
    kinds = {w.kind for w in weaknesses}
    assert WeaknessKind.HARD_SECTION in kinds


def test_detect_late_bias() -> None:
    outcomes = [
        NoteOutcome(i * 0.5, 60, True, 40.0) for i in range(10)
    ]
    report = SessionReport(
        session_id=uuid4(),
        song_id=uuid4(),
        outcomes=outcomes,
        sections=build_sections_from_outcomes(outcomes),
    )
    weaknesses = detect_weaknesses(report)
    assert any(w.kind is WeaknessKind.SYSTEMATIC_LATE for w in weaknesses)


def test_recommendation_engine() -> None:
    report = _report_with_hard_section()
    profile = SkillProfile()
    engine = RecommendationEngine()
    recs = engine.recommend(report, profile)
    assert len(recs) >= 1
    assert recs[0].exercise.kind in (
        ExerciseKind.SECTION_LOOP,
        ExerciseKind.TEMPO_RAMP,
        ExerciseKind.SIGHT_READING,
    )
    plan = engine.build_plan(report, profile)
    assert plan.exercise_count >= 1
    # Skills were updated
    assert profile.get(SkillId.PITCH_ACCURACY).sample_count >= 1


def test_skill_level_ema() -> None:
    profile = SkillProfile()
    skill = profile.get(SkillId.RHYTHM_TIMING)
    skill.update(0.5)
    skill.update(1.0)
    assert 0.5 < skill.level < 1.0
    assert skill.sample_count == 2

"""Build a rich SessionReport from engine session results."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fretflow.engine.events import HitEvent, MissEvent
from fretflow.practice.session_report import (
    NoteOutcome,
    SessionReport,
    build_sections_from_outcomes,
)

if TYPE_CHECKING:
    from fretflow.engine.session_runner import SessionRunner


def report_from_runner(
    runner: SessionRunner,
    *,
    window_seconds: float = 4.0,
) -> SessionReport:
    """Convert a SessionRunner into a SessionReport."""
    outcomes: list[NoteOutcome] = []

    for hit in runner._hit_events:
        outcomes.append(
            NoteOutcome(
                expected_seconds=hit.expected_seconds,
                midi_pitch=hit.midi_pitch,
                hit=True,
                offset_ms=hit.offset_ms,
            )
        )

    for miss in runner._miss_events:
        outcomes.append(
            NoteOutcome(
                expected_seconds=miss.expected_seconds,
                midi_pitch=miss.midi_pitch,
                hit=False,
                offset_ms=None,
            )
        )

    outcomes.sort(key=lambda o: o.expected_seconds)
    sections = build_sections_from_outcomes(outcomes, window_seconds=window_seconds)

    session = runner.build_session()
    return SessionReport(
        session_id=session.id,
        song_id=session.song_id,
        outcomes=outcomes,
        sections=sections,
        tempo_factor=session.tempo_factor,
        duration_seconds=session.duration_seconds,
        score=session.score,
        max_combo=session.max_combo,
    )


def report_from_events(
    *,
    session_id: UUID,
    song_id: UUID,
    hits: list[HitEvent],
    misses: list[MissEvent],
    tempo_factor: float = 1.0,
    duration_seconds: float = 0.0,
    score: int = 0,
    max_combo: int = 0,
    window_seconds: float = 4.0,
) -> SessionReport:
    outcomes: list[NoteOutcome] = []
    for hit in hits:
        outcomes.append(
            NoteOutcome(
                expected_seconds=hit.expected_seconds,
                midi_pitch=hit.midi_pitch,
                hit=True,
                offset_ms=hit.offset_ms,
            )
        )
    for miss in misses:
        outcomes.append(
            NoteOutcome(
                expected_seconds=miss.expected_seconds,
                midi_pitch=miss.midi_pitch,
                hit=False,
                offset_ms=None,
            )
        )
    outcomes.sort(key=lambda o: o.expected_seconds)
    return SessionReport(
        session_id=session_id,
        song_id=song_id,
        outcomes=outcomes,
        sections=build_sections_from_outcomes(outcomes, window_seconds=window_seconds),
        tempo_factor=tempo_factor,
        duration_seconds=duration_seconds,
        score=score,
        max_combo=max_combo,
    )

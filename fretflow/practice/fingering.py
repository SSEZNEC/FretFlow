"""FingeringEngine — left-hand finger suggestions for guitar notes."""

from __future__ import annotations

from dataclasses import dataclass

from fretflow.core.models import Note
from fretflow.practice.fretboard import (
    STANDARD_TUNING,
    FretMarker,
    FretPosition,
    midi_to_preferred_position,
    note_to_position,
)


@dataclass(slots=True)
class FingeringConfig:
    """Parameters controlling finger assignment heuristics."""

    hand_span: int = 4          # frets the hand can cover comfortably
    prefer_open: bool = True
    max_position_jump: int = 5  # frets between successive positions


@dataclass(slots=True)
class FingeringEngine:
    """Assign fingers and resolve missing string/fret data.

    Pure domain logic: no UI, no I/O.
    Uses Guitar Pro finger data when present; otherwise computes
    a coherent assignment that minimises position jumps.
    """

    config: FingeringConfig | None = None
    tuning: tuple[int, ...] = STANDARD_TUNING

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = FingeringConfig()

    def assign_sequence(self, notes: list[Note]) -> list[Note]:
        """Return new Note objects with string/fret/finger filled in.

        Does not mutate the input list.
        """
        if not notes:
            return []

        result: list[Note] = []
        prev_fret: int | None = None
        prev_finger: int | None = None
        hand_root: int | None = None  # lowest fret of current position

        for note in notes:
            string, fret = self._resolve_position(note, prev_fret)
            finger = note.finger

            if finger is None:
                finger = self._suggest_finger(fret, hand_root, prev_finger)

            # Update hand root (position on the neck)
            if hand_root is None or abs(fret - hand_root) > self.config.hand_span:
                hand_root = max(0, fret - 1) if fret > 0 else 0

            if fret == 0:
                finger = 0  # open string

            new_note = Note(
                start_seconds=note.start_seconds,
                duration_seconds=note.duration_seconds,
                midi_pitch=note.midi_pitch,
                string=string,
                fret=fret,
                technique=note.technique,
                finger=finger,
                velocity=note.velocity,
            )
            result.append(new_note)
            prev_fret = fret
            prev_finger = finger if finger and finger > 0 else prev_finger

        return result

    def positions_at(
        self,
        notes: list[Note],
        time_seconds: float,
        lookahead_seconds: float = 1.5,
        window: float = 0.08,
    ) -> list[FretPosition]:
        """Fret positions for notes around *time_seconds*."""
        assigned = self.assign_sequence(notes)
        positions: list[FretPosition] = []

        for note in assigned:
            delta = note.start_seconds - time_seconds
            if -window <= delta <= window:
                marker = FretMarker.CURRENT
            elif window < delta <= lookahead_seconds:
                marker = FretMarker.NEXT
            elif -note.duration_seconds <= delta < -window:
                marker = FretMarker.HELD
            else:
                continue
            positions.append(note_to_position(note, marker))

        return positions

    def _resolve_position(
        self, note: Note, prev_fret: int | None
    ) -> tuple[int, int]:
        if note.string is not None and note.fret is not None:
            return note.string, note.fret

        preferred_min = 0
        preferred_max = 12
        if prev_fret is not None:
            preferred_min = max(0, prev_fret - self.config.max_position_jump)
            preferred_max = min(24, prev_fret + self.config.max_position_jump)

        return midi_to_preferred_position(
            note.midi_pitch,
            tuning=self.tuning,
            preferred_fret_min=preferred_min,
            preferred_fret_max=preferred_max,
        )

    def _suggest_finger(
        self,
        fret: int,
        hand_root: int | None,
        prev_finger: int | None,
    ) -> int:
        """Map fret to finger 1..4 within the current hand position."""
        if fret == 0:
            return 0
        root = hand_root if hand_root is not None else max(0, fret - 1)
        offset = fret - root
        if offset <= 0:
            return 1
        if offset == 1:
            return 1
        if offset == 2:
            return 2
        if offset == 3:
            return 3
        return 4

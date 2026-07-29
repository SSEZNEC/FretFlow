"""Domain model of a guitar fretboard state at a point in time."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from fretflow.core.models import Note, Technique


class FretMarker(Enum):
    """Visual role of a position on the fretboard."""

    CURRENT = auto()   # note to play now
    NEXT = auto()      # upcoming note
    HELD = auto()      # still held / chord tone
    ERROR = auto()     # wrong note played
    PREVIEW = auto()   # further lookahead


# Standard tuning MIDI for open strings (string 1 = high E … 6 = low E)
STANDARD_TUNING: tuple[int, ...] = (64, 59, 55, 50, 45, 40)  # E B G D A E


@dataclass(slots=True, frozen=True)
class FretPosition:
    """A single fretted position on the neck."""

    string: int   # 1..6
    fret: int     # 0..24 (0 = open)
    finger: int | None = None  # 1..4
    midi_pitch: int | None = None
    marker: FretMarker = FretMarker.CURRENT
    technique: Technique = Technique.NONE

    def __post_init__(self) -> None:
        if not 1 <= self.string <= 6:
            raise ValueError(f"string must be 1..6, got {self.string}")
        if not 0 <= self.fret <= 24:
            raise ValueError(f"fret must be 0..24, got {self.fret}")


@dataclass(slots=True)
class FretboardState:
    """Snapshot of highlighted positions at song time *t*."""

    time_seconds: float
    positions: list[FretPosition] = field(default_factory=list)
    chord_name: str | None = None
    position_label: str | None = None  # e.g. "Position V"

    @property
    def current(self) -> list[FretPosition]:
        return [p for p in self.positions if p.marker is FretMarker.CURRENT]

    @property
    def next_notes(self) -> list[FretPosition]:
        return [p for p in self.positions if p.marker is FretMarker.NEXT]


def midi_to_preferred_position(
    midi_pitch: int,
    tuning: tuple[int, ...] = STANDARD_TUNING,
    preferred_fret_min: int = 0,
    preferred_fret_max: int = 12,
) -> tuple[int, int]:
    """Return (string, fret) for a MIDI pitch using preferred fret range.

    Prefers mid-neck positions; falls back to any valid fret 0..24.
    """
    candidates: list[tuple[int, int, int]] = []  # cost, string, fret
    for string_idx, open_pitch in enumerate(tuning):
        fret = midi_pitch - open_pitch
        if 0 <= fret <= 24:
            string = string_idx + 1  # 1-based
            if preferred_fret_min <= fret <= preferred_fret_max:
                cost = abs(fret - 5)  # prefer around fret 5
            else:
                cost = 50 + abs(fret - 5)
            candidates.append((cost, string, fret))
    if not candidates:
        # Out of range — clamp to closest
        return 1, max(0, min(24, midi_pitch - tuning[0]))
    candidates.sort()
    _, string, fret = candidates[0]
    return string, fret


def note_to_position(note: Note, marker: FretMarker = FretMarker.CURRENT) -> FretPosition:
    """Convert a domain Note into a FretPosition, estimating string/fret if missing."""
    string = note.string
    fret = note.fret
    if string is None or fret is None:
        string, fret = midi_to_preferred_position(note.midi_pitch)
    return FretPosition(
        string=string,
        fret=fret,
        finger=note.finger,
        midi_pitch=note.midi_pitch,
        marker=marker,
        technique=note.technique,
    )

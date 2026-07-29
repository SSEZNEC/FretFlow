"""Session / engine events (lightweight, no UI dependency)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from fretflow.engine.judgment import Judgment


class EventKind(Enum):
    NOTE_HIT = auto()
    NOTE_MISS = auto()
    SECTION_END = auto()
    SESSION_END = auto()


@dataclass(slots=True, frozen=True)
class HitEvent:
    expected_seconds: float
    played_seconds: float
    midi_pitch: int
    judgment: Judgment
    offset_ms: float
    combo: int
    score: int


@dataclass(slots=True, frozen=True)
class MissEvent:
    expected_seconds: float
    midi_pitch: int
    combo: int


@dataclass(slots=True, frozen=True)
class PlayedNoteEvent:
    """Raw input from keyboard / MIDI / audio adapters."""

    midi_pitch: int
    time_seconds: float  # song time when the note was played
    velocity: int = 80

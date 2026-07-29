"""Core domain models.

These dataclasses form the pure domain layer. They must not depend on
PySide6, sounddevice, SQLAlchemy, Mido or PyGuitarPro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from uuid import UUID, uuid4


class Technique(Enum):
    """Playing techniques that may be attached to a note."""

    NONE = auto()
    BEND = auto()
    SLIDE = auto()
    HAMMER_ON = auto()
    PULL_OFF = auto()
    VIBRATO = auto()
    PALM_MUTE = auto()
    HARMONIC = auto()
    TAP = auto()


@dataclass(slots=True)
class Note:
    """A single note or chord tone on the timeline.

    Time is in seconds from the start of the song.
    Pitch is MIDI note number (0-127).
    Duration is in seconds.
    """

    start_seconds: float
    duration_seconds: float
    midi_pitch: int
    string: int | None = None  # 1 = high E … 6 = low E (guitar convention)
    fret: int | None = None
    technique: Technique = Technique.NONE
    velocity: int = 80

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be >= 0")
        if not 0 <= self.midi_pitch <= 127:
            raise ValueError("midi_pitch must be in 0..127")


@dataclass(slots=True)
class Measure:
    """A measure (bar) containing notes."""

    index: int
    start_seconds: float
    duration_seconds: float
    numerator: int = 4
    denominator: int = 4
    notes: list[Note] = field(default_factory=list)


@dataclass(slots=True)
class Track:
    """A single instrument track within a song."""

    name: str
    midi_channel: int = 0
    measures: list[Measure] = field(default_factory=list)
    is_guitar: bool = True
    tuning: tuple[int, ...] = (64, 59, 55, 50, 45, 40)  # EADGBE MIDI

    @property
    def notes(self) -> list[Note]:
        """Flattened list of all notes in the track."""
        result: list[Note] = []
        for measure in self.measures:
            result.extend(measure.notes)
        return result


@dataclass(slots=True)
class Song:
    """Internal representation of a playable song."""

    title: str
    artist: str = ""
    tempo_bpm: float = 120.0
    tracks: list[Track] = field(default_factory=list)
    source_path: Path | None = None
    id: UUID = field(default_factory=uuid4)
    duration_seconds: float = 0.0
    key: str = ""
    time_signature: str = "4/4"

    def primary_track(self) -> Track | None:
        """Return the first guitar track, or the first track if none marked."""
        for track in self.tracks:
            if track.is_guitar:
                return track
        return self.tracks[0] if self.tracks else None


@dataclass(slots=True)
class Session:
    """A practice session record."""

    song_id: UUID
    started_at: float  # Unix timestamp
    duration_seconds: float = 0.0
    notes_hit: int = 0
    notes_missed: int = 0
    notes_expected: int = 0
    score: int = 0
    max_combo: int = 0
    tempo_factor: float = 1.0
    section_start_seconds: float | None = None
    section_end_seconds: float | None = None
    id: UUID = field(default_factory=uuid4)

    @property
    def accuracy(self) -> float:
        """Hit rate in [0, 1]."""
        total = self.notes_hit + self.notes_missed
        if total == 0:
            return 0.0
        return self.notes_hit / total


@dataclass(slots=True)
class PerformanceReport:
    """Summary produced after a session."""

    session_id: UUID
    accuracy: float
    average_offset_ms: float
    hard_sections: list[tuple[float, float]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    notes_expected: int = 0
    notes_hit: int = 0
    notes_missed: int = 0
    max_combo: int = 0
    score: int = 0

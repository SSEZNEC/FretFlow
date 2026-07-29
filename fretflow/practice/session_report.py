"""Domain: rich session analysis for the coach.

SessionReport aggregates per-section statistics so the coach can reason
about where and why the player struggled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import UUID


class SectionDifficulty(Enum):
    EASY = auto()
    MODERATE = auto()
    HARD = auto()
    CRITICAL = auto()


@dataclass(slots=True, frozen=True)
class NoteOutcome:
    """Single expected note result."""

    expected_seconds: float
    midi_pitch: int
    hit: bool
    offset_ms: float | None  # None if missed
    measure_index: int | None = None


@dataclass(slots=True)
class SectionStats:
    """Aggregated stats for a time window inside a song."""

    start_seconds: float
    end_seconds: float
    notes_expected: int = 0
    notes_hit: int = 0
    notes_missed: int = 0
    average_offset_ms: float = 0.0
    measure_index: int | None = None

    @property
    def accuracy(self) -> float:
        total = self.notes_hit + self.notes_missed
        if total == 0:
            return 0.0
        return self.notes_hit / total

    @property
    def difficulty(self) -> SectionDifficulty:
        acc = self.accuracy
        if acc >= 0.9:
            return SectionDifficulty.EASY
        if acc >= 0.75:
            return SectionDifficulty.MODERATE
        if acc >= 0.5:
            return SectionDifficulty.HARD
        return SectionDifficulty.CRITICAL


@dataclass(slots=True)
class SessionReport:
    """Full analysis of one practice session (deterministic)."""

    session_id: UUID
    song_id: UUID
    outcomes: list[NoteOutcome] = field(default_factory=list)
    sections: list[SectionStats] = field(default_factory=list)
    tempo_factor: float = 1.0
    duration_seconds: float = 0.0
    score: int = 0
    max_combo: int = 0
    technique_tags_seen: list[str] = field(default_factory=list)

    @property
    def notes_expected(self) -> int:
        return len(self.outcomes)

    @property
    def notes_hit(self) -> int:
        return sum(1 for o in self.outcomes if o.hit)

    @property
    def notes_missed(self) -> int:
        return sum(1 for o in self.outcomes if not o.hit)

    @property
    def accuracy(self) -> float:
        total = self.notes_hit + self.notes_missed
        if total == 0:
            return 0.0
        return self.notes_hit / total

    @property
    def average_offset_ms(self) -> float:
        offsets = [
            o.offset_ms for o in self.outcomes if o.hit and o.offset_ms is not None
        ]
        if not offsets:
            return 0.0
        return sum(offsets) / len(offsets)

    def hard_sections(self, max_accuracy: float = 0.75) -> list[SectionStats]:
        return [
            s
            for s in self.sections
            if s.accuracy <= max_accuracy and s.notes_expected > 0
        ]

    def late_bias_ms(self) -> float:
        """Positive = systematically late."""
        return self.average_offset_ms


def build_sections_from_outcomes(
    outcomes: list[NoteOutcome],
    window_seconds: float = 4.0,
) -> list[SectionStats]:
    """Bucket outcomes into fixed-size time windows (pure helper)."""
    if not outcomes or window_seconds <= 0:
        return []

    max_t = max(o.expected_seconds for o in outcomes)
    sections: list[SectionStats] = []
    t = 0.0
    while t <= max_t:
        end = t + window_seconds
        bucket = [o for o in outcomes if t <= o.expected_seconds < end]
        if bucket:
            hits = [o for o in bucket if o.hit]
            offsets = [o.offset_ms for o in hits if o.offset_ms is not None]
            sections.append(
                SectionStats(
                    start_seconds=t,
                    end_seconds=end,
                    notes_expected=len(bucket),
                    notes_hit=len(hits),
                    notes_missed=len(bucket) - len(hits),
                    average_offset_ms=(
                        sum(offsets) / len(offsets) if offsets else 0.0
                    ),
                )
            )
        t = end
    return sections

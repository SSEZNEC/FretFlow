"""Domain: practice exercises derived from songs or techniques."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import UUID, uuid4


class ExerciseKind(Enum):
    SECTION_LOOP = auto()
    TEMPO_RAMP = auto()
    TECHNIQUE_DRILL = auto()
    SIGHT_READING = auto()
    CUSTOM = auto()


@dataclass(slots=True)
class Exercise:
    """A concrete, playable unit of practice."""

    title: str
    kind: ExerciseKind
    song_id: UUID | None = None
    track_index: int = 0
    section_start_seconds: float | None = None
    section_end_seconds: float | None = None
    tempo_factor: float = 0.75
    target_accuracy: float = 0.85
    target_repetitions: int = 3
    technique_tags: list[str] = field(default_factory=list)
    instructions: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not 0.25 <= self.tempo_factor <= 2.0:
            raise ValueError("tempo_factor must be between 0.25 and 2.0")
        if not 0.0 <= self.target_accuracy <= 1.0:
            raise ValueError("target_accuracy must be in 0..1")
        if self.target_repetitions < 1:
            raise ValueError("target_repetitions must be >= 1")
        if (
            self.section_start_seconds is not None
            and self.section_end_seconds is not None
            and self.section_end_seconds <= self.section_start_seconds
        ):
            raise ValueError("section_end must be > section_start")

    @property
    def has_section(self) -> bool:
        return (
            self.section_start_seconds is not None
            and self.section_end_seconds is not None
        )

    @property
    def duration_hint_seconds(self) -> float | None:
        if not self.has_section:
            return None
        assert self.section_start_seconds is not None
        assert self.section_end_seconds is not None
        return (self.section_end_seconds - self.section_start_seconds) / self.tempo_factor

"""Practice session settings."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class PracticeSettings:
    """User-controlled parameters for a practice run."""

    song_id: UUID
    track_index: int = 0
    tempo_factor: float = 1.0  # 0.5 … 1.0 typical
    section_start_seconds: float | None = None
    section_end_seconds: float | None = None
    loop_enabled: bool = False
    metronome_enabled: bool = False
    metronome_bpm: float | None = None  # None = use song tempo * factor

    def __post_init__(self) -> None:
        if not 0.25 <= self.tempo_factor <= 2.0:
            raise ValueError("tempo_factor must be between 0.25 and 2.0")
        if self.section_start_seconds is not None and self.section_end_seconds is not None:
            if self.section_end_seconds <= self.section_start_seconds:
                raise ValueError("section_end must be > section_start")

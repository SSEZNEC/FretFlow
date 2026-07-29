"""A/B loop controller."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LoopRegion:
    """Inclusive start, exclusive end in song seconds."""

    start_seconds: float
    end_seconds: float
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("loop end must be > start")

    def contains(self, song_time: float) -> bool:
        return self.start_seconds <= song_time < self.end_seconds

    def should_wrap(self, song_time: float) -> bool:
        return self.enabled and song_time >= self.end_seconds

    def wrap_target(self) -> float:
        return self.start_seconds

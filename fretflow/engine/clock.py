"""Deterministic game/practice clock.

Time is always in song seconds. The tempo factor scales wall-clock mapping
without changing the song timeline coordinates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto


class ClockState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


@dataclass(slots=True)
class GameClock:
    """Playhead over a song timeline.

    ``song_time`` is the current position in the song (seconds).
    ``tempo_factor`` of 0.5 means half speed (song advances half as fast).
    """

    duration_seconds: float = 0.0
    tempo_factor: float = 1.0
    song_time: float = 0.0
    state: ClockState = ClockState.STOPPED
    _wall_anchor: float = field(default=0.0, repr=False)
    _song_anchor: float = field(default=0.0, repr=False)

    def __post_init__(self) -> None:
        if self.tempo_factor <= 0:
            raise ValueError("tempo_factor must be > 0")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be >= 0")

    def start(self) -> None:
        self.state = ClockState.RUNNING
        self._wall_anchor = time.perf_counter()
        self._song_anchor = self.song_time

    def pause(self) -> None:
        if self.state is ClockState.RUNNING:
            self.song_time = self.current_time()
            self.state = ClockState.PAUSED

    def resume(self) -> None:
        if self.state is ClockState.PAUSED:
            self.start()

    def stop(self) -> None:
        if self.state is ClockState.RUNNING:
            self.song_time = self.current_time()
        self.state = ClockState.STOPPED

    def seek(self, song_seconds: float) -> None:
        """Jump to an absolute position in the song (clamped)."""
        song_seconds = max(0.0, min(song_seconds, self.duration_seconds))
        self.song_time = song_seconds
        if self.state is ClockState.RUNNING:
            self._wall_anchor = time.perf_counter()
            self._song_anchor = song_seconds

    def set_tempo_factor(self, factor: float) -> None:
        if factor <= 0:
            raise ValueError("tempo_factor must be > 0")
        # Capture current song time before changing rate
        if self.state is ClockState.RUNNING:
            self.song_time = self.current_time()
            self._wall_anchor = time.perf_counter()
            self._song_anchor = self.song_time
        self.tempo_factor = factor

    def current_time(self) -> float:
        """Return the current song position in seconds."""
        if self.state is not ClockState.RUNNING:
            return self.song_time
        elapsed_wall = time.perf_counter() - self._wall_anchor
        t = self._song_anchor + elapsed_wall * self.tempo_factor
        if self.duration_seconds > 0 and t >= self.duration_seconds:
            self.song_time = self.duration_seconds
            self.state = ClockState.STOPPED
            return self.song_time
        return t

    @property
    def is_running(self) -> bool:
        return self.state is ClockState.RUNNING

    @property
    def is_finished(self) -> bool:
        return (
            self.duration_seconds > 0
            and self.current_time() >= self.duration_seconds
            and self.state is ClockState.STOPPED
        )

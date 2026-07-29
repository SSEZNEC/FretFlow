"""Simple metronome click scheduler (no audio output — emits beat times)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Metronome:
    """Generates beat timestamps in song-time coordinates."""

    bpm: float
    enabled: bool = True
    beats_per_bar: int = 4

    def __post_init__(self) -> None:
        if self.bpm <= 0:
            raise ValueError("bpm must be > 0")

    @property
    def beat_interval_seconds(self) -> float:
        return 60.0 / self.bpm

    def beat_index_at(self, song_time: float) -> int:
        """Zero-based beat index at or before song_time."""
        if song_time < 0:
            return 0
        return int(song_time / self.beat_interval_seconds)

    def next_beat_time(self, song_time: float) -> float:
        idx = self.beat_index_at(song_time)
        t = idx * self.beat_interval_seconds
        if t <= song_time + 1e-9:
            t = (idx + 1) * self.beat_interval_seconds
        return t

    def is_downbeat(self, beat_index: int) -> bool:
        return beat_index % self.beats_per_bar == 0

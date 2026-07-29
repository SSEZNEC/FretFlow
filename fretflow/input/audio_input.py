"""Bridge audio pipeline events into the session runner time base."""

from __future__ import annotations

from fretflow.audio.pipeline import AudioPipeline
from fretflow.audio.types import AudioConfig
from fretflow.engine.events import PlayedNoteEvent


class AudioInputAdapter:
    """Maps capture-clock times to song-time using the game clock."""

    def __init__(
        self,
        pipeline: AudioPipeline | None = None,
        config: AudioConfig | None = None,
    ) -> None:
        self.pipeline = pipeline or AudioPipeline(config=config)
        self._song_time_provider = lambda: 0.0

    def set_song_time_provider(self, provider) -> None:
        """provider() -> current song time in seconds."""
        self._song_time_provider = provider

    def process(self) -> PlayedNoteEvent | None:
        """Detect and remap time onto the song timeline."""
        song_t = self._song_time_provider()
        event = self.pipeline.process_latest(song_t)
        if event is None:
            return None
        # Event time is already set to the time we passed (song time)
        return PlayedNoteEvent(
            midi_pitch=event.midi_pitch,
            time_seconds=song_t,
            velocity=event.velocity,
        )

"""High-level audio → PlayedNoteEvent pipeline."""

from __future__ import annotations

import logging
from typing import Callable

import numpy as np

from fretflow.audio.buffer import CircularBuffer
from fretflow.audio.pitch import PitchDetector, YinDetector
from fretflow.audio.types import AudioConfig, PitchEstimate
from fretflow.audio.validation import NoteValidator
from fretflow.engine.events import PlayedNoteEvent

logger = logging.getLogger("fretflow.audio.pipeline")

NoteCallback = Callable[[PlayedNoteEvent], None]


class AudioPipeline:
    """Processes audio blocks into validated note events.

    Designed so the heavy work is outside the audio callback:
    the capture callback only stores samples; ``process_block`` can be
    called from a timer / worker.
    """

    def __init__(
        self,
        config: AudioConfig | None = None,
        detector: PitchDetector | None = None,
        validator: NoteValidator | None = None,
    ) -> None:
        self.config = config or AudioConfig()
        self.detector = detector or YinDetector(
            noise_rms=self.config.noise_threshold_rms,
        )
        self.validator = validator or NoteValidator(
            min_confidence=self.config.min_confidence,
        )
        self.buffer = CircularBuffer(self.config.sample_rate * 2)
        self._on_note: NoteCallback | None = None
        self._last_estimate: PitchEstimate | None = None

    def set_note_callback(self, callback: NoteCallback | None) -> None:
        self._on_note = callback

    def on_audio_block(self, samples: np.ndarray, time_seconds: float) -> None:
        """Lightweight: store samples only (safe for audio callback)."""
        self.buffer.write(samples)

    def process_latest(self, time_seconds: float) -> PlayedNoteEvent | None:
        """Run detection on the latest window. Call from UI timer / worker."""
        window = self.buffer.read_latest(self.config.block_size * 2)
        if window.size < self.config.block_size:
            return None
        estimate = self.detector.detect(window, self.config.sample_rate, time_seconds)
        self._last_estimate = estimate
        event = self.validator.process(estimate)
        if event and self._on_note:
            self._on_note(event)
        return event

    @property
    def last_estimate(self) -> PitchEstimate | None:
        return self._last_estimate

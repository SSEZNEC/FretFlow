"""Sample playback adapter — optional sounddevice, always works offline."""

from __future__ import annotations

import logging
import threading
from typing import Protocol

import numpy as np

logger = logging.getLogger("fretflow.audio.sample_player")


class AudioSink(Protocol):
    def play(self, samples: np.ndarray, sample_rate: int) -> None: ...
    def stop(self) -> None: ...


class NullSink:
    """Silent sink for tests and headless environments."""

    def __init__(self) -> None:
        self.last: np.ndarray | None = None
        self.play_count = 0

    def play(self, samples: np.ndarray, sample_rate: int) -> None:
        self.last = samples
        self.play_count += 1

    def stop(self) -> None:
        pass


class SoundDeviceSink:
    """Non-blocking playback via sounddevice (when PortAudio is available)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def play(self, samples: np.ndarray, sample_rate: int) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:
            logger.debug("sounddevice unavailable: %s", exc)
            return
        with self._lock:
            try:
                sd.play(samples, sample_rate, blocking=False)
            except Exception as exc:
                logger.warning("Playback failed: %s", exc)

    def stop(self) -> None:
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass


def default_sink() -> AudioSink:
    try:
        import sounddevice as sd  # noqa: F401
        return SoundDeviceSink()
    except Exception:
        return NullSink()

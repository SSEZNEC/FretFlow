"""Audio capture adapter — optional sounddevice, always has a simulator."""

from __future__ import annotations

import logging
import time
from typing import Callable

import numpy as np

from fretflow.audio.buffer import CircularBuffer
from fretflow.audio.types import AudioConfig
from fretflow.core.errors import AudioDeviceError

logger = logging.getLogger("fretflow.audio.capture")

# Callback receives (samples: np.ndarray, time_seconds: float)
BlockCallback = Callable[[np.ndarray, float], None]


class SimulatedCapture:
    """Feeds synthetic blocks on demand — no hardware."""

    def __init__(self, config: AudioConfig | None = None) -> None:
        self.config = config or AudioConfig()
        self._running = False
        self._callback: BlockCallback | None = None
        self._time = 0.0
        self.buffer = CircularBuffer(self.config.sample_rate * 2)

    def list_devices(self) -> list[str]:
        return ["[simulated] default"]

    def start(self, callback: BlockCallback | None = None) -> None:
        self._callback = callback
        self._running = True
        self._time = 0.0
        logger.info("SimulatedCapture started (sr=%d)", self.config.sample_rate)

    def stop(self) -> None:
        self._running = False
        self._callback = None

    def push_block(self, samples: np.ndarray) -> None:
        """Inject a block (tests / offline processing)."""
        if not self._running:
            return
        samples = np.asarray(samples, dtype=np.float32).ravel()
        self.buffer.write(samples)
        if self._callback:
            self._callback(samples, self._time)
        self._time += samples.size / self.config.sample_rate

    @property
    def is_running(self) -> bool:
        return self._running


class SoundDeviceCapture:
    """Real microphone capture via sounddevice (optional dependency)."""

    def __init__(self, config: AudioConfig | None = None, device: int | str | None = None) -> None:
        self.config = config or AudioConfig()
        self.device = device
        self._stream = None
        self._callback: BlockCallback | None = None
        self._start_wall = 0.0
        self.buffer = CircularBuffer(self.config.sample_rate * 2)

    def list_devices(self) -> list[str]:
        try:
            import sounddevice as sd
        except Exception as exc:
            raise AudioDeviceError(f"sounddevice unavailable: {exc}") from exc
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                result.append(f"{i}: {d['name']}")
        return result

    def start(self, callback: BlockCallback | None = None) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:
            raise AudioDeviceError(
                "sounddevice / PortAudio not available. "
                "Use SimulatedCapture or install PortAudio."
            ) from exc

        self._callback = callback
        self._start_wall = time.perf_counter()

        def _audio_cb(indata, frames, time_info, status):  # noqa: ANN001
            # Keep this callback light — no disk, no heavy logs
            if status:
                logger.debug("Audio status: %s", status)
            mono = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
            self.buffer.write(mono)
            t = time.perf_counter() - self._start_wall
            # Compensate calibrated latency (shift perceived time backward)
            t -= self.config.latency_ms / 1000.0
            if self._callback:
                self._callback(mono, t)

        try:
            self._stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                blocksize=self.config.block_size,
                channels=self.config.channels,
                dtype="float32",
                device=self.device,
                callback=_audio_cb,
            )
            self._stream.start()
        except Exception as exc:
            raise AudioDeviceError(f"Cannot open audio device: {exc}") from exc
        logger.info("SoundDeviceCapture started (device=%s)", self.device)

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._callback = None

    @property
    def is_running(self) -> bool:
        return self._stream is not None

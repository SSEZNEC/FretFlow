"""Audio domain types — pure data, no I/O."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PitchEstimate:
    """Probabilistic pitch detection result.

    Units:
      - frequency_hz: Hz
      - midi_pitch: float (may be fractional for cents)
      - confidence: 0..1
      - time_seconds: capture-clock seconds (not song time)
    """

    frequency_hz: float
    midi_pitch: float
    confidence: float
    time_seconds: float
    rms: float = 0.0

    @property
    def midi_rounded(self) -> int:
        return int(round(self.midi_pitch))

    @property
    def cents_offset(self) -> float:
        """Deviation from nearest MIDI note in cents."""
        return (self.midi_pitch - self.midi_rounded) * 100.0


@dataclass(slots=True)
class AudioConfig:
    sample_rate: int = 44100
    block_size: int = 1024
    channels: int = 1
    noise_threshold_rms: float = 0.01
    min_confidence: float = 0.6
    latency_ms: float = 0.0  # calibrated input latency compensation

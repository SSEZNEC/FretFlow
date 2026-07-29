"""Guitar sample banks — synthesised tones (no external sample files required).

Real WAV banks can replace the synthesizer later without changing the API.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

import numpy as np

from fretflow.audio.pitch import midi_to_hz


class Timbre(str, Enum):
    CLEAN = "clean"
    ACOUSTIC = "acoustic"
    CRUNCH = "crunch"
    JAZZ = "jazz"
    CLASSICAL = "classical"



def _envelope(n: int, attack: float, decay: float, sr: int) -> np.ndarray:
    env = np.ones(n, dtype=np.float32)
    a = max(1, int(attack * sr))
    d = max(1, int(decay * sr))
    env[:a] = np.linspace(0, 1, a, dtype=np.float32)
    if d < n:
        tail = np.linspace(1, 0.05, min(d, n - a), dtype=np.float32)
        env[a : a + len(tail)] = tail
        if a + len(tail) < n:
            rest = n - (a + len(tail))
            env[a + len(tail) :] = np.linspace(0.05, 0.0, rest, dtype=np.float32)
    return env


def _karplus_strong(freq: float, duration: float, sr: int, brightness: float = 0.5) -> np.ndarray:
    """Simple plucked-string synthesis."""
    n = max(1, int(duration * sr))
    period = max(2, int(sr / freq))
    buf = (np.random.randn(period).astype(np.float32) * 0.5)
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        out[i] = buf[i % period]
        avg = 0.5 * (buf[i % period] + buf[(i + 1) % period])
        buf[i % period] = avg * (0.994 + 0.004 * brightness)
    return out


def synthesize_note(
    midi_pitch: int,
    duration: float = 0.4,
    velocity: float = 0.8,
    timbre: Timbre = Timbre.CLEAN,
    sample_rate: int = 22050,
) -> np.ndarray:
    """Return a mono float32 buffer for one guitar-like note."""
    freq = midi_to_hz(float(midi_pitch))
    sr = sample_rate
    duration = max(0.05, min(duration, 3.0))
    velocity = max(0.05, min(velocity, 1.0))

    if timbre in (Timbre.ACOUSTIC, Timbre.CLASSICAL):
        wave = _karplus_strong(freq, duration, sr, brightness=0.7)
        # Add soft harmonic
        t = np.arange(len(wave)) / sr
        wave = wave + 0.15 * np.sin(2 * np.pi * freq * 2 * t).astype(np.float32)
    elif timbre is Timbre.CRUNCH:
        t = np.arange(int(duration * sr)) / sr
        wave = np.sin(2 * np.pi * freq * t).astype(np.float32)
        wave = np.tanh(wave * 3.0).astype(np.float32)  # soft clip
        wave = wave * _envelope(len(wave), 0.005, duration * 0.8, sr)
    elif timbre is Timbre.JAZZ:
        t = np.arange(int(duration * sr)) / sr
        wave = (
            0.7 * np.sin(2 * np.pi * freq * t)
            + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
            + 0.1 * np.sin(2 * np.pi * freq * 3 * t)
        ).astype(np.float32)
        wave = wave * _envelope(len(wave), 0.01, duration * 0.9, sr)
    else:  # CLEAN
        wave = _karplus_strong(freq, duration, sr, brightness=0.55)

    wave = wave * velocity
    peak = float(np.max(np.abs(wave))) or 1.0
    if peak > 0.95:
        wave = wave * (0.95 / peak)
    return wave.astype(np.float32)


class SoundBank:
    """Preloads synthesised notes for low-latency playback."""

    def __init__(
        self,
        timbre: Timbre = Timbre.CLEAN,
        sample_rate: int = 22050,
        midi_min: int = 40,
        midi_max: int = 88,
    ) -> None:
        self.timbre = timbre
        self.sample_rate = sample_rate
        self.midi_min = midi_min
        self.midi_max = midi_max
        self._cache: dict[tuple[int, int], np.ndarray] = {}  # (midi, dur_ms)

    def get(self, midi_pitch: int, duration: float = 0.4) -> np.ndarray:
        dur_ms = int(round(duration * 1000))
        key = (midi_pitch, dur_ms)
        if key not in self._cache:
            self._cache[key] = synthesize_note(
                midi_pitch, duration=duration, timbre=self.timbre, sample_rate=self.sample_rate
            )
        return self._cache[key]

    def preload_range(self, duration: float = 0.35) -> None:
        for midi in range(self.midi_min, self.midi_max + 1):
            self.get(midi, duration)

    def chord(self, midi_pitches: list[int], duration: float = 0.6) -> np.ndarray:
        if not midi_pitches:
            return np.zeros(1, dtype=np.float32)
        waves = [self.get(m, duration) for m in midi_pitches]
        n = max(len(w) for w in waves)
        mix = np.zeros(n, dtype=np.float32)
        for w in waves:
            mix[: len(w)] += w
        peak = float(np.max(np.abs(mix))) or 1.0
        if peak > 0.95:
            mix *= 0.95 / peak
        return mix

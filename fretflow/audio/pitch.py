"""Pitch detection algorithms (pure NumPy — no microphone required)."""

from __future__ import annotations

import math
from typing import Protocol

import numpy as np

from fretflow.audio.types import PitchEstimate


def hz_to_midi(frequency_hz: float) -> float:
    """Convert frequency (Hz) to fractional MIDI note number."""
    if frequency_hz <= 0:
        return 0.0
    return 69.0 + 12.0 * math.log2(frequency_hz / 440.0)


def midi_to_hz(midi_pitch: float) -> float:
    return 440.0 * (2.0 ** ((midi_pitch - 69.0) / 12.0))


class PitchDetector(Protocol):
    """Interchangeable pitch detector."""

    def detect(self, samples: np.ndarray, sample_rate: int, time_seconds: float) -> PitchEstimate | None:
        """Return a pitch estimate or None if silence / unreliable."""
        ...


def _rms(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))


class YinDetector:
    """Autocorrelation pitch detector with subharmonic rejection.

    Designed for monophonic guitar notes. Fully offline-testable.
    """

    def __init__(
        self,
        fmin: float = 80.0,
        fmax: float = 1200.0,
        noise_rms: float = 0.01,
    ) -> None:
        self.fmin = fmin
        self.fmax = fmax
        self.noise_rms = noise_rms

    def detect(
        self, samples: np.ndarray, sample_rate: int, time_seconds: float
    ) -> PitchEstimate | None:
        if samples.ndim > 1:
            samples = samples[:, 0]
        samples = np.asarray(samples, dtype=np.float64)
        rms = _rms(samples)
        if rms < self.noise_rms or samples.size < 128:
            return None

        # Remove DC
        samples = samples - np.mean(samples)

        tau_min = max(2, int(sample_rate / self.fmax))
        tau_max = min(samples.size // 2 - 1, int(sample_rate / self.fmin))
        if tau_max <= tau_min + 2:
            return None

        # Normalized autocorrelation for lags tau_min..tau_max
        n = samples.size
        # Use FFT-based autocorrelation for speed and stability
        nfft = 1
        while nfft < 2 * n:
            nfft *= 2
        spectrum = np.fft.rfft(samples, n=nfft)
        autocorr = np.fft.irfft(spectrum * np.conj(spectrum), n=nfft)[:n]
        if autocorr[0] <= 0:
            return None
        autocorr = autocorr / autocorr[0]

        # Find peaks in the lag range; prefer the smallest lag (highest freq)
        # whose correlation is a local maximum above 0.4
        candidates: list[tuple[int, float]] = []
        for tau in range(tau_min + 1, tau_max - 1):
            c = float(autocorr[tau])
            if c > 0.4 and c >= autocorr[tau - 1] and c >= autocorr[tau + 1]:
                candidates.append((tau, c))

        if not candidates:
            # Fallback: global max in range
            region = autocorr[tau_min:tau_max]
            if region.size == 0:
                return None
            idx = int(np.argmax(region))
            tau = tau_min + idx
            corr = float(region[idx])
            if corr < 0.3:
                return None
        else:
            # Take highest frequency (smallest tau) with good correlation
            # but prefer stronger peaks if within 1.5x lag of the first
            candidates.sort(key=lambda x: x[0])
            tau, corr = candidates[0]
            for t2, c2 in candidates[1:]:
                if t2 < tau * 1.9 and c2 > corr * 1.05:
                    # Stronger peak at roughly harmonic — still prefer fundamental
                    # only switch if much stronger
                    if c2 > corr + 0.15:
                        tau, corr = t2, c2
                elif t2 >= tau * 1.9:
                    break

        # Parabolic interpolation around tau
        if 1 <= tau < autocorr.size - 1:
            a, b, c = float(autocorr[tau - 1]), float(autocorr[tau]), float(autocorr[tau + 1])
            denom = a - 2 * b + c
            if abs(denom) > 1e-12:
                delta = 0.5 * (a - c) / denom
                if abs(delta) < 1:
                    tau_f = tau + delta
                else:
                    tau_f = float(tau)
            else:
                tau_f = float(tau)
        else:
            tau_f = float(tau)

        frequency = sample_rate / tau_f
        if not (self.fmin <= frequency <= self.fmax):
            return None

        confidence = min(1.0, max(0.0, corr))
        midi = hz_to_midi(frequency)
        return PitchEstimate(
            frequency_hz=frequency,
            midi_pitch=midi,
            confidence=confidence,
            time_seconds=time_seconds,
            rms=rms,
        )


class SimulatedDetector:
    """Detector that returns a scripted pitch sequence (for tests / demos)."""

    def __init__(self, estimates: list[PitchEstimate] | None = None) -> None:
        self._estimates = list(estimates or [])
        self._index = 0

    def push(self, estimate: PitchEstimate) -> None:
        self._estimates.append(estimate)

    def detect(
        self, samples: np.ndarray, sample_rate: int, time_seconds: float
    ) -> PitchEstimate | None:
        if self._index >= len(self._estimates):
            return None
        est = self._estimates[self._index]
        self._index += 1
        return PitchEstimate(
            frequency_hz=est.frequency_hz,
            midi_pitch=est.midi_pitch,
            confidence=est.confidence,
            time_seconds=time_seconds,
            rms=est.rms,
        )

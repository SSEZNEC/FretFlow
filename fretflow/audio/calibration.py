"""Latency calibration helpers."""

from __future__ import annotations

from dataclasses import dataclass

from fretflow.audio.types import AudioConfig


@dataclass(slots=True)
class CalibrationResult:
    latency_ms: float
    method: str
    notes: str = ""


def apply_latency(config: AudioConfig, latency_ms: float) -> AudioConfig:
    """Return a copy of config with updated latency compensation."""
    return AudioConfig(
        sample_rate=config.sample_rate,
        block_size=config.block_size,
        channels=config.channels,
        noise_threshold_rms=config.noise_threshold_rms,
        min_confidence=config.min_confidence,
        latency_ms=latency_ms,
    )


def estimate_latency_from_offsets(offsets_ms: list[float]) -> CalibrationResult:
    """Estimate systematic latency from a list of (played - expected) offsets.

    If the player is consistently late by ~X ms, the input path may need
    an X ms compensation (or the player needs practice — calibration UI
    should make this distinction clear).
    """
    if not offsets_ms:
        return CalibrationResult(0.0, "none", "No samples")
    median = sorted(offsets_ms)[len(offsets_ms) // 2]
    # Only suggest compensation for large systematic delay
    if abs(median) < 15:
        return CalibrationResult(0.0, "median", f"Offset médian {median:.0f} ms — OK")
    return CalibrationResult(
        latency_ms=median,
        method="median",
        notes=f"Offset médian {median:.0f} ms — compensation proposée",
    )

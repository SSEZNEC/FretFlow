"""Audio DSP tests — synthetic signals only, no microphone."""

from __future__ import annotations

import numpy as np
import pytest

from fretflow.audio.buffer import CircularBuffer
from fretflow.audio.calibration import estimate_latency_from_offsets
from fretflow.audio.capture import SimulatedCapture
from fretflow.audio.pipeline import AudioPipeline
from fretflow.audio.pitch import YinDetector, hz_to_midi, midi_to_hz
from fretflow.audio.types import AudioConfig, PitchEstimate
from fretflow.audio.validation import NoteValidator
from fretflow.audio.pitch import SimulatedDetector


def _sine(freq_hz: float, duration_s: float, sr: int = 44100, amp: float = 0.5) -> np.ndarray:
    t = np.arange(int(sr * duration_s)) / sr
    return (amp * np.sin(2 * np.pi * freq_hz * t)).astype(np.float32)


def test_hz_midi_roundtrip() -> None:
    assert hz_to_midi(440.0) == pytest.approx(69.0)
    assert midi_to_hz(69.0) == pytest.approx(440.0)
    assert hz_to_midi(midi_to_hz(60)) == pytest.approx(60.0, abs=0.01)


def test_circular_buffer() -> None:
    buf = CircularBuffer(10)
    buf.write(np.arange(5, dtype=np.float32))
    assert buf.filled == 5
    latest = buf.read_latest(3)
    assert list(latest) == [2.0, 3.0, 4.0]
    buf.write(np.arange(10, 18, dtype=np.float32))
    assert buf.filled == 10
    latest = buf.read_latest(4)
    assert latest.size == 4


def test_yin_detects_a4() -> None:
    sr = 44100
    samples = _sine(440.0, 0.1, sr=sr)
    det = YinDetector(noise_rms=0.001)
    est = det.detect(samples, sr, time_seconds=0.0)
    assert est is not None
    assert est.frequency_hz == pytest.approx(440.0, rel=0.05)
    assert est.midi_rounded == 69
    assert est.confidence > 0.5


def test_yin_detects_c4() -> None:
    sr = 44100
    freq = midi_to_hz(60)  # C4 ≈ 261.63
    samples = _sine(freq, 0.15, sr=sr)
    det = YinDetector(noise_rms=0.001)
    est = det.detect(samples, sr, 0.0)
    assert est is not None
    assert est.midi_rounded == 60


def test_yin_silence() -> None:
    samples = np.zeros(2048, dtype=np.float32)
    assert YinDetector().detect(samples, 44100, 0.0) is None


def test_validator_debounce() -> None:
    v = NoteValidator(min_frames=3, min_confidence=0.5, cooldown_seconds=0.0)
    # Two frames — not enough
    for t in (0.0, 0.01):
        e = PitchEstimate(261.6, 60.0, 0.9, t, rms=0.1)
        assert v.process(e) is None
    # Third frame — emit
    event = v.process(PitchEstimate(261.6, 60.0, 0.9, 0.02, rms=0.1))
    assert event is not None
    assert event.midi_pitch == 60


def test_pipeline_with_sine() -> None:
    sr = 44100
    config = AudioConfig(sample_rate=sr, block_size=1024, noise_threshold_rms=0.001)
    pipe = AudioPipeline(config=config, detector=YinDetector(noise_rms=0.001))
    samples = _sine(midi_to_hz(64), 0.2, sr=sr)  # E4
    # Feed in blocks
    for i in range(0, len(samples), 1024):
        block = samples[i : i + 1024]
        if block.size < 512:
            break
        t = i / sr
        pipe.on_audio_block(block, t)
        event = pipe.process_latest(t)
        # May need a few blocks before detection stabilizes
    # Force process full buffer
    event = pipe.process_latest(0.15)
    # Detection should have some estimate
    assert pipe.last_estimate is not None or event is not None


def test_simulated_capture() -> None:
    cap = SimulatedCapture(AudioConfig(sample_rate=8000, block_size=256))
    received = []
    cap.start(callback=lambda s, t: received.append((s.size, t)))
    cap.push_block(np.ones(256, dtype=np.float32) * 0.1)
    cap.push_block(np.ones(256, dtype=np.float32) * 0.1)
    assert len(received) == 2
    assert received[0][0] == 256
    cap.stop()


def test_latency_estimate() -> None:
    result = estimate_latency_from_offsets([40.0, 42.0, 38.0, 41.0])
    assert result.latency_ms == pytest.approx(41.0, abs=2)
    ok = estimate_latency_from_offsets([5.0, -3.0, 2.0])
    assert ok.latency_ms == 0.0


def test_simulated_detector() -> None:
    est = PitchEstimate(440.0, 69.0, 0.95, 0.0)
    det = SimulatedDetector([est, est])
    r1 = det.detect(np.zeros(100), 44100, 1.0)
    assert r1 is not None and r1.midi_rounded == 69
    r2 = det.detect(np.zeros(100), 44100, 2.0)
    assert r2 is not None
    assert det.detect(np.zeros(100), 44100, 3.0) is None

"""Audio capture, DSP and pitch detection adapters."""

from fretflow.audio.buffer import CircularBuffer
from fretflow.audio.calibration import CalibrationResult, apply_latency, estimate_latency_from_offsets
from fretflow.audio.capture import SimulatedCapture, SoundDeviceCapture
from fretflow.audio.pipeline import AudioPipeline
from fretflow.audio.pitch import PitchDetector, SimulatedDetector, YinDetector, hz_to_midi, midi_to_hz
from fretflow.audio.types import AudioConfig, PitchEstimate
from fretflow.audio.validation import NoteValidator

__all__ = [
    "AudioConfig",
    "AudioPipeline",
    "CalibrationResult",
    "CircularBuffer",
    "NoteValidator",
    "PitchDetector",
    "PitchEstimate",
    "SimulatedCapture",
    "SimulatedDetector",
    "SoundDeviceCapture",
    "YinDetector",
    "apply_latency",
    "estimate_latency_from_offsets",
    "hz_to_midi",
    "midi_to_hz",
]

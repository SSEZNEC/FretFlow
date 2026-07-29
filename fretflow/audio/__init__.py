"""Audio capture, DSP, reference playback and pitch detection."""

from fretflow.audio.buffer import CircularBuffer
from fretflow.audio.calibration import CalibrationResult, apply_latency, estimate_latency_from_offsets
from fretflow.audio.capture import SimulatedCapture, SoundDeviceCapture
from fretflow.audio.pipeline import AudioPipeline
from fretflow.audio.pitch import PitchDetector, SimulatedDetector, YinDetector, hz_to_midi, midi_to_hz
from fretflow.audio.reference_audio import ReferenceAudioEngine, ReferenceMode
from fretflow.audio.sample_player import NullSink, default_sink
from fretflow.audio.sound_bank import SoundBank, Timbre, synthesize_note
from fretflow.audio.types import AudioConfig, PitchEstimate
from fretflow.audio.validation import NoteValidator

__all__ = [
    "AudioConfig",
    "AudioPipeline",
    "CalibrationResult",
    "CircularBuffer",
    "NullSink",
    "NoteValidator",
    "PitchDetector",
    "PitchEstimate",
    "ReferenceAudioEngine",
    "ReferenceMode",
    "SimulatedCapture",
    "SimulatedDetector",
    "SoundBank",
    "SoundDeviceCapture",
    "Timbre",
    "YinDetector",
    "apply_latency",
    "default_sink",
    "estimate_latency_from_offsets",
    "hz_to_midi",
    "midi_to_hz",
    "synthesize_note",
]

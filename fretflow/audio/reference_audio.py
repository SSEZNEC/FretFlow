"""ReferenceAudioEngine — plays the expected sound before/during practice."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto

import numpy as np

from fretflow.audio.sample_player import AudioSink, NullSink, default_sink
from fretflow.audio.sound_bank import SoundBank, Timbre
from fretflow.core.models import Note

logger = logging.getLogger("fretflow.audio.reference")


class ReferenceMode(Enum):
    OFF = auto()
    NOTE = auto()            # each expected note
    CHORD = auto()           # only simultaneous groups
    TEMPO = auto()           # only during loop repetitions
    LEARN = auto()           # all notes (learning mode)
    SILENT_ON_ERROR = auto() # only after a miss
    DEMO = auto()            # play-through demonstration
    ASSIST = auto()          # note just before it arrives
    CORRECTION = auto()      # alias of SILENT_ON_ERROR


@dataclass(slots=True)
class ReferenceAudioEngine:
    """Independent of gameplay — pure audio preview of expected notes."""

    mode: ReferenceMode = ReferenceMode.NOTE
    timbre: Timbre = Timbre.CLEAN
    volume: float = 0.7
    bank: SoundBank | None = None
    sink: AudioSink | None = None
    _played_ids: set[int] = field(default_factory=set, init=False, repr=False)
    _in_loop: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.bank is None:
            self.bank = SoundBank(timbre=self.timbre)
        if self.sink is None:
            self.sink = default_sink()

    def set_mode(self, mode: ReferenceMode) -> None:
        self.mode = mode
        self._played_ids.clear()

    def set_in_loop(self, active: bool) -> None:
        self._in_loop = active

    def preload(self) -> None:
        assert self.bank is not None
        self.bank.preload_range()
        logger.info("Reference bank preloaded (%s)", self.timbre.value)

    def reset(self) -> None:
        self._played_ids.clear()

    def on_note_approaching(self, note: Note, lead_time: float = 0.0) -> None:
        """Call when playhead approaches a note (once per note)."""
        if self.mode is ReferenceMode.OFF:
            return
        if self.mode is ReferenceMode.TEMPO and not self._in_loop:
            return
        if self.mode in (ReferenceMode.SILENT_ON_ERROR, ReferenceMode.CORRECTION):
            return  # only plays on miss via on_miss
        if self.mode is ReferenceMode.CHORD:
            return  # handled by on_chord
        # DEMO / ASSIST / NOTE / LEARN all play approaching notes

        note_id = id(note) if not hasattr(note, "start_seconds") else (
            hash((note.start_seconds, note.midi_pitch, note.string, note.fret))
        )
        if note_id in self._played_ids:
            return
        self._played_ids.add(note_id)
        self._play_note(note)

    def on_chord(self, notes: list[Note]) -> None:
        if self.mode not in (ReferenceMode.CHORD, ReferenceMode.LEARN, ReferenceMode.NOTE):
            if self.mode is not ReferenceMode.CHORD:
                return
        if self.mode is ReferenceMode.OFF:
            return
        if not notes:
            return
        key = hash(tuple(sorted((n.start_seconds, n.midi_pitch) for n in notes)))
        if key in self._played_ids:
            return
        self._played_ids.add(key)
        assert self.bank is not None and self.sink is not None
        duration = max(n.duration_seconds for n in notes)
        mix = self.bank.chord([n.midi_pitch for n in notes], duration=min(duration, 1.2))
        mix = mix * self.volume
        self.sink.play(mix, self.bank.sample_rate)

    def on_miss(self, midi_pitch: int, duration: float = 0.3) -> None:
        if self.mode in (ReferenceMode.SILENT_ON_ERROR, ReferenceMode.CORRECTION):
            self._play_midi(midi_pitch, duration)

    def play_demo(self, midi_pitch: int, duration: float = 0.5) -> None:
        """Always play — used by ear-training / call-and-response."""
        self._play_midi(midi_pitch, duration)

    def play_demo_chord(self, midi_pitches: list[int], duration: float = 0.7) -> None:
        assert self.bank is not None and self.sink is not None
        mix = self.bank.chord(midi_pitches, duration=duration) * self.volume
        self.sink.play(mix, self.bank.sample_rate)

    def stop(self) -> None:
        if self.sink:
            self.sink.stop()

    def _play_note(self, note: Note) -> None:
        self._play_midi(note.midi_pitch, max(0.12, min(note.duration_seconds, 1.5)))

    def _play_midi(self, midi_pitch: int, duration: float) -> None:
        assert self.bank is not None and self.sink is not None
        samples = self.bank.get(midi_pitch, duration) * self.volume
        self.sink.play(samples, self.bank.sample_rate)

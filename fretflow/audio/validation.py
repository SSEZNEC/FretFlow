"""Validate pitch estimates into discrete played notes."""

from __future__ import annotations

from dataclasses import dataclass, field

from fretflow.audio.types import PitchEstimate
from fretflow.engine.events import PlayedNoteEvent


@dataclass(slots=True)
class NoteValidator:
    """Debounce pitch estimates into stable note-on events.

    Requires *min_frames* consecutive frames on the same MIDI pitch
    (within *cent_tolerance*) before emitting a PlayedNoteEvent.
    """

    min_frames: int = 3
    cent_tolerance: float = 50.0
    min_confidence: float = 0.55
    cooldown_seconds: float = 0.12

    _current_midi: int | None = field(default=None, init=False, repr=False)
    _streak: int = field(default=0, init=False, repr=False)
    _last_emit_time: float = field(default=-1e9, init=False, repr=False)
    _emitted_for_streak: bool = field(default=False, init=False, repr=False)

    def process(self, estimate: PitchEstimate | None) -> PlayedNoteEvent | None:
        if estimate is None or estimate.confidence < self.min_confidence:
            self._reset_streak()
            return None

        midi = estimate.midi_rounded
        cents = abs(estimate.cents_offset)
        if cents > self.cent_tolerance:
            self._reset_streak()
            return None

        if midi == self._current_midi:
            self._streak += 1
        else:
            self._current_midi = midi
            self._streak = 1
            self._emitted_for_streak = False

        if (
            self._streak >= self.min_frames
            and not self._emitted_for_streak
            and (estimate.time_seconds - self._last_emit_time) >= self.cooldown_seconds
        ):
            self._emitted_for_streak = True
            self._last_emit_time = estimate.time_seconds
            return PlayedNoteEvent(
                midi_pitch=midi,
                time_seconds=estimate.time_seconds,
                velocity=int(min(127, max(1, estimate.rms * 500))),
            )
        return None

    def _reset_streak(self) -> None:
        self._current_midi = None
        self._streak = 0
        self._emitted_for_streak = False

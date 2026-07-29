"""Detect simultaneous notes and name common guitar chords."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from fretflow.core.models import Note
from fretflow.practice.fretboard import FretMarker, FretPosition, note_to_position

# Pitch class -> note name
_PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Interval sets (from root) for common chords
_CHORD_TEMPLATES: dict[str, frozenset[int]] = {
    "": frozenset({0, 4, 7}),           # major
    "m": frozenset({0, 3, 7}),          # minor
    "5": frozenset({0, 7}),             # power chord
    "7": frozenset({0, 4, 7, 10}),      # dominant 7
    "maj7": frozenset({0, 4, 7, 11}),
    "m7": frozenset({0, 3, 7, 10}),
    "dim": frozenset({0, 3, 6}),
    "aug": frozenset({0, 4, 8}),
    "sus2": frozenset({0, 2, 7}),
    "sus4": frozenset({0, 5, 7}),
}


@dataclass(slots=True, frozen=True)
class ChordVoicing:
    """A set of simultaneous notes identified as a chord."""

    name: str
    root_pc: int
    start_seconds: float
    notes: tuple[Note, ...]
    positions: tuple[FretPosition, ...] = ()

    @property
    def is_power_chord(self) -> bool:
        return self.name.endswith("5") and "maj" not in self.name and "m" not in self.name


@dataclass(slots=True)
class ChordAnalyser:
    """Group near-simultaneous notes into chord voicings."""

    window_seconds: float = 0.05  # notes within this gap form a chord

    def analyse(self, notes: list[Note]) -> list[ChordVoicing]:
        if not notes:
            return []
        sorted_notes = sorted(notes, key=lambda n: n.start_seconds)
        groups: list[list[Note]] = []
        current: list[Note] = [sorted_notes[0]]

        for note in sorted_notes[1:]:
            if note.start_seconds - current[0].start_seconds <= self.window_seconds:
                current.append(note)
            else:
                groups.append(current)
                current = [note]
        groups.append(current)

        voicings: list[ChordVoicing] = []
        for group in groups:
            if len(group) < 2:
                continue
            name, root = self._name_chord(group)
            positions = tuple(
                note_to_position(n, FretMarker.CURRENT) for n in group
            )
            voicings.append(
                ChordVoicing(
                    name=name,
                    root_pc=root,
                    start_seconds=group[0].start_seconds,
                    notes=tuple(group),
                    positions=positions,
                )
            )
        return voicings

    def _name_chord(self, notes: list[Note]) -> tuple[str, int]:
        pcs = sorted({n.midi_pitch % 12 for n in notes})
        if not pcs:
            return "?", 0

        best_name = "chord"
        best_root = pcs[0]
        best_score = -1

        for root in pcs:
            intervals = frozenset((pc - root) % 12 for pc in pcs)
            for suffix, template in _CHORD_TEMPLATES.items():
                if template.issubset(intervals):
                    score = len(template)
                    if score > best_score:
                        best_score = score
                        best_root = root
                        best_name = f"{_PC_NAMES[root]}{suffix}"

        if best_score < 0:
            # Unknown — list pitch classes
            names = [_PC_NAMES[pc] for pc in pcs]
            return "+".join(names), pcs[0]
        return best_name, best_root

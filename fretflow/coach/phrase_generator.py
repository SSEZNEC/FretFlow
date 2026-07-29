"""Call & response — generate short phrases for the player to repeat."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fretflow.audio.reference_audio import ReferenceAudioEngine
from fretflow.core.models import Note
from fretflow.practice.fingering import FingeringEngine


@dataclass(slots=True)
class Phrase:
    """A short melodic fragment."""

    notes: list[Note]
    id: UUID = field(default_factory=uuid4)

    @property
    def duration_seconds(self) -> float:
        if not self.notes:
            return 0.0
        last = self.notes[-1]
        return last.start_seconds + last.duration_seconds


@dataclass(slots=True)
class CallResponseResult:
    phrase_id: UUID
    notes_expected: int
    notes_matched: int
    reaction_ms: float | None = None

    @property
    def accuracy(self) -> float:
        if self.notes_expected == 0:
            return 0.0
        return self.notes_matched / self.notes_expected


@dataclass(slots=True)
class PhraseGenerator:
    """Builds pedagogically simple phrases (scale fragments, sequences)."""

    midi_min: int = 60
    midi_max: int = 72
    note_duration: float = 0.35

    def scale_fragment(self, length: int = 4, ascending: bool = True) -> Phrase:
        root = random.randint(self.midi_min, max(self.midi_min, self.midi_max - length))
        # Major scale steps
        steps = [0, 2, 4, 5, 7, 9, 11, 12]
        pitches = []
        for i in range(length):
            idx = i if ascending else (length - 1 - i)
            pitches.append(root + steps[idx % len(steps)])
        notes = [
            Note(
                start_seconds=i * self.note_duration,
                duration_seconds=self.note_duration * 0.9,
                midi_pitch=p,
            )
            for i, p in enumerate(pitches)
        ]
        notes = FingeringEngine().assign_sequence(notes)
        return Phrase(notes=notes)

    def repeat_motif(self, length: int = 3) -> Phrase:
        pitch = random.randint(self.midi_min, self.midi_max)
        notes = [
            Note(
                start_seconds=i * self.note_duration,
                duration_seconds=self.note_duration * 0.85,
                midi_pitch=pitch + (0 if i % 2 == 0 else 2),
            )
            for i in range(length)
        ]
        return Phrase(notes=FingeringEngine().assign_sequence(notes))


@dataclass(slots=True)
class CallResponseSession:
    """Play a phrase, then score the player's attempt."""

    generator: PhraseGenerator = field(default_factory=PhraseGenerator)
    engine: ReferenceAudioEngine | None = None
    current: Phrase | None = None
    results: list[CallResponseResult] = field(default_factory=list)

    def next_phrase(self, length: int = 4) -> Phrase:
        self.current = self.generator.scale_fragment(length=length)
        return self.current

    def play_call(self) -> None:
        if self.current is None or self.engine is None:
            return
        for note in self.current.notes:
            self.engine.play_demo(note.midi_pitch, duration=note.duration_seconds)

    def score_response(self, played: list[int]) -> CallResponseResult:
        if self.current is None:
            return CallResponseResult(uuid4(), 0, 0)
        expected = [n.midi_pitch % 12 for n in self.current.notes]
        got = [p % 12 for p in played]
        matched = sum(1 for a, b in zip(expected, got) if a == b)
        # also count if same multiset length
        result = CallResponseResult(
            phrase_id=self.current.id,
            notes_expected=len(expected),
            notes_matched=matched,
        )
        self.results.append(result)
        return result

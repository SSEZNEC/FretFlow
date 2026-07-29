"""Ear-training exercises — hear a sound, find it on the neck, play it."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import UUID, uuid4

from fretflow.audio.reference_audio import ReferenceAudioEngine
from fretflow.coach.skills import SkillId
from fretflow.core.models import Note
from fretflow.practice.fretboard import midi_to_preferred_position


class EarExerciseKind(Enum):
    SINGLE_NOTE = auto()
    INTERVAL = auto()
    CHORD = auto()


@dataclass(slots=True)
class EarChallenge:
    """One prompt for the player."""

    kind: EarExerciseKind
    target_midis: list[int]
    prompt: str
    id: UUID = field(default_factory=uuid4)

    @property
    def primary_midi(self) -> int:
        return self.target_midis[0]


@dataclass(slots=True)
class EarResult:
    challenge_id: UUID
    correct: bool
    played_midi: int | None
    reaction_ms: float | None
    skill: SkillId = SkillId.PITCH_ACCURACY


@dataclass(slots=True)
class EarTrainingSession:
    """Stateful ear-training loop (pure logic + optional audio)."""

    engine: ReferenceAudioEngine | None = None
    midi_min: int = 52  # E3
    midi_max: int = 76  # E5
    challenges: list[EarChallenge] = field(default_factory=list)
    results: list[EarResult] = field(default_factory=list)
    _current: EarChallenge | None = field(default=None, init=False, repr=False)
    _prompt_time: float | None = field(default=None, init=False, repr=False)

    def next_challenge(self, kind: EarExerciseKind = EarExerciseKind.SINGLE_NOTE) -> EarChallenge:
        if kind is EarExerciseKind.SINGLE_NOTE:
            midi = random.randint(self.midi_min, self.midi_max)
            string, fret = midi_to_preferred_position(midi)
            challenge = EarChallenge(
                kind=kind,
                target_midis=[midi],
                prompt=f"Écoute et retrouve la note (indice: corde {string} possible).",
            )
        elif kind is EarExerciseKind.INTERVAL:
            root = random.randint(self.midi_min, self.midi_max - 7)
            interval = random.choice([3, 4, 5, 7])  # m3, M3, 4th, 5th
            challenge = EarChallenge(
                kind=kind,
                target_midis=[root, root + interval],
                prompt="Écoute l'intervalle, puis joue les deux notes.",
            )
        else:
            # Simple major triad root position
            root = random.choice([48, 50, 52, 53, 55, 57, 59])  # C..B
            challenge = EarChallenge(
                kind=kind,
                target_midis=[root, root + 4, root + 7],
                prompt="Écoute l'accord majeur, puis reconstitue-le.",
            )
        self.challenges.append(challenge)
        self._current = challenge
        return challenge

    def play_prompt(self) -> None:
        if self._current is None or self.engine is None:
            return
        if len(self._current.target_midis) == 1:
            self.engine.play_demo(self._current.target_midis[0], duration=0.6)
        else:
            self.engine.play_demo_chord(self._current.target_midis, duration=0.8)

    def submit(self, played_midi: int, now_seconds: float = 0.0) -> EarResult:
        if self._current is None:
            return EarResult(uuid4(), False, played_midi, None)
        target = self._current.primary_midi
        # Allow enharmonic / octave tolerance for single notes: same pitch class
        if self._current.kind is EarExerciseKind.SINGLE_NOTE:
            correct = (played_midi % 12) == (target % 12)
        else:
            correct = played_midi in self._current.target_midis or (
                played_midi % 12 in {m % 12 for m in self._current.target_midis}
            )
        result = EarResult(
            challenge_id=self._current.id,
            correct=correct,
            played_midi=played_midi,
            reaction_ms=None,
        )
        self.results.append(result)
        return result

    @property
    def accuracy(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.correct) / len(self.results)

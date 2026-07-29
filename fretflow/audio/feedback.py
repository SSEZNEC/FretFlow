"""Pitch feedback labels for the teacher (correct / sharp / flat / unstable)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from fretflow.audio.types import PitchEstimate


class PitchFeedback(Enum):
    CORRECT = auto()
    SHARP = auto()      # too high
    FLAT = auto()       # too low
    UNSTABLE = auto()
    SILENCE = auto()


@dataclass(slots=True, frozen=True)
class FeedbackResult:
    kind: PitchFeedback
    cents: float
    label: str


def compare_pitch(
    estimate: PitchEstimate | None,
    expected_midi: int,
    *,
    correct_cents: float = 25.0,
    unstable_confidence: float = 0.45,
) -> FeedbackResult:
    """Compare a live pitch estimate to the expected MIDI note."""
    if estimate is None:
        return FeedbackResult(PitchFeedback.SILENCE, 0.0, "…")
    if estimate.confidence < unstable_confidence:
        return FeedbackResult(PitchFeedback.UNSTABLE, 0.0, "≈ Instable")

    cents = (estimate.midi_pitch - expected_midi) * 100.0
    if abs(cents) <= correct_cents:
        return FeedbackResult(PitchFeedback.CORRECT, cents, "✔ Correct")
    if cents > 0:
        return FeedbackResult(PitchFeedback.SHARP, cents, f"▲ Trop aigu ({cents:+.0f} ¢)")
    return FeedbackResult(PitchFeedback.FLAT, cents, f"▼ Trop grave ({cents:+.0f} ¢)")

"""Note timing judgment (Perfect / Great / Good / Miss)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from fretflow.core.config import JudgmentWindows
from fretflow.core.time_units import seconds_to_ms


class Judgment(Enum):
    PERFECT = auto()
    GREAT = auto()
    GOOD = auto()
    MISS = auto()


@dataclass(slots=True, frozen=True)
class JudgmentResult:
    judgment: Judgment
    offset_ms: float  # played - expected, positive = late

    @property
    def is_hit(self) -> bool:
        return self.judgment is not Judgment.MISS


def judge_note(
    expected_seconds: float,
    played_seconds: float,
    windows: JudgmentWindows | None = None,
) -> JudgmentResult:
    """Compare a played onset to an expected onset.

    Windows are half-widths in milliseconds around the expected time.
    """
    windows = windows or JudgmentWindows()
    offset_ms = seconds_to_ms(played_seconds - expected_seconds)
    abs_ms = abs(offset_ms)

    if abs_ms <= windows.perfect_ms:
        return JudgmentResult(Judgment.PERFECT, offset_ms)
    if abs_ms <= windows.great_ms:
        return JudgmentResult(Judgment.GREAT, offset_ms)
    if abs_ms <= windows.good_ms:
        return JudgmentResult(Judgment.GOOD, offset_ms)
    return JudgmentResult(Judgment.MISS, offset_ms)

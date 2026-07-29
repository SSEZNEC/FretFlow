"""Score and combo helpers (pure functions)."""

from __future__ import annotations

from fretflow.engine.judgment import Judgment

_SCORE_TABLE = {
    Judgment.PERFECT: 100,
    Judgment.GREAT: 75,
    Judgment.GOOD: 50,
    Judgment.MISS: 0,
}


def points_for(judgment: Judgment, combo: int) -> int:
    """Base points multiplied by a simple combo factor."""
    base = _SCORE_TABLE[judgment]
    if judgment is Judgment.MISS:
        return 0
    multiplier = 1.0 + min(combo, 50) * 0.02
    return int(base * multiplier)


def next_combo(current: int, judgment: Judgment) -> int:
    if judgment is Judgment.MISS:
        return 0
    return current + 1

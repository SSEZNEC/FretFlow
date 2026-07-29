"""Ghost hand — virtual left-hand guide on the fretboard.

Shows recommended finger placements and the next movement.
Can be hidden, fingers-only, or full position markers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from fretflow.practice.fretboard import FretMarker, FretPosition


class GhostHandMode(Enum):
    HIDDEN = auto()
    FINGERS_ONLY = auto()
    POSITIONS = auto()
    FULL = auto()


@dataclass(slots=True)
class GhostHandState:
    """What the virtual hand should display right now."""

    mode: GhostHandMode = GhostHandMode.FULL
    current: list[FretPosition] | None = None
    next_positions: list[FretPosition] | None = None
    message: str = ""

    def visible_positions(self) -> list[FretPosition]:
        if self.mode is GhostHandMode.HIDDEN:
            return []
        result: list[FretPosition] = []
        if self.current:
            result.extend(self.current)
        if self.mode is GhostHandMode.FULL and self.next_positions:
            for p in self.next_positions:
                result.append(
                    FretPosition(
                        string=p.string,
                        fret=p.fret,
                        finger=p.finger,
                        midi_pitch=p.midi_pitch,
                        marker=FretMarker.PREVIEW,
                        technique=p.technique,
                    )
                )
        return result

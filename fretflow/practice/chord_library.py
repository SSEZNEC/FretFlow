"""Common open and barre chord shapes for teaching."""

from __future__ import annotations

from dataclasses import dataclass

from fretflow.practice.fretboard import FretMarker, FretPosition


@dataclass(slots=True, frozen=True)
class ChordShape:
    name: str
    positions: tuple[FretPosition, ...]  # string, fret, finger
    aliases: tuple[str, ...] = ()


def _p(string: int, fret: int, finger: int) -> FretPosition:
    return FretPosition(string=string, fret=fret, finger=finger, marker=FretMarker.CURRENT)


# Open-position shapes (string 1 = high E)
OPEN_CHORDS: dict[str, ChordShape] = {
    "C": ChordShape("C", (_p(5, 3, 3), _p(4, 2, 2), _p(3, 0, 0), _p(2, 1, 1), _p(1, 0, 0))),
    "D": ChordShape("D", (_p(3, 2, 1), _p(2, 3, 3), _p(1, 2, 2))),
    "E": ChordShape("E", (_p(6, 0, 0), _p(5, 2, 2), _p(4, 2, 3), _p(3, 1, 1), _p(2, 0, 0), _p(1, 0, 0))),
    "G": ChordShape("G", (_p(6, 3, 2), _p(5, 2, 1), _p(4, 0, 0), _p(3, 0, 0), _p(2, 0, 0), _p(1, 3, 3))),
    "A": ChordShape("A", (_p(5, 0, 0), _p(4, 2, 2), _p(3, 2, 3), _p(2, 2, 4), _p(1, 0, 0))),
    "Am": ChordShape("Am", (_p(5, 0, 0), _p(4, 2, 2), _p(3, 2, 3), _p(2, 1, 1), _p(1, 0, 0))),
    "Em": ChordShape("Em", (_p(6, 0, 0), _p(5, 2, 2), _p(4, 2, 3), _p(3, 0, 0), _p(2, 0, 0), _p(1, 0, 0))),
    "Dm": ChordShape("Dm", (_p(3, 2, 2), _p(2, 3, 3), _p(1, 1, 1))),
}


def lookup_chord(name: str) -> ChordShape | None:
    key = name.strip()
    if key in OPEN_CHORDS:
        return OPEN_CHORDS[key]
    # Try without suffix variations
    for k, shape in OPEN_CHORDS.items():
        if key.startswith(k):
            return shape
    return None


def list_open_chords() -> list[str]:
    return list(OPEN_CHORDS.keys())

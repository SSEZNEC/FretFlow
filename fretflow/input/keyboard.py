"""Keyboard → PlayedNoteEvent mapping for testing without a guitar."""

from __future__ import annotations

# Simple home-row mapping for demos (QWERTY)
# a s d f g h j k  →  C4 D4 E4 F4 G4 A4 B4 C5
DEFAULT_KEY_MAP: dict[str, int] = {
    "a": 60,  # C4
    "s": 62,  # D4
    "d": 64,  # E4
    "f": 65,  # F4
    "g": 67,  # G4
    "h": 69,  # A4
    "j": 71,  # B4
    "k": 72,  # C5
    "w": 61,  # C#4
    "e": 63,  # D#4
    "t": 66,  # F#4
    "y": 68,  # G#4
    "u": 70,  # A#4
}


def key_to_midi(key: str, key_map: dict[str, int] | None = None) -> int | None:
    """Return MIDI pitch for a key character, or None if unmapped."""
    mapping = key_map or DEFAULT_KEY_MAP
    return mapping.get(key.lower())

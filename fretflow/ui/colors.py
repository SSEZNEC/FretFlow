"""UI color palette (dark theme). Presentation only — no game logic."""

from __future__ import annotations

# Highway
BG = "#1a1a2e"
LANE = "#16213e"
HIT_LINE = "#e94560"
GRID = "#0f3460"

# Note gem colors by pitch class (C=0 … B=11)
NOTE_COLORS = [
    "#e74c3c",  # C  red
    "#e67e22",  # C#
    "#f1c40f",  # D  yellow
    "#2ecc71",  # D#
    "#1abc9c",  # E  teal
    "#3498db",  # F  blue
    "#9b59b6",  # F#
    "#e91e63",  # G  pink
    "#ff5722",  # G#
    "#00bcd4",  # A  cyan
    "#8bc34a",  # A#
    "#ff9800",  # B
]

JUDGMENT_COLORS = {
    "PERFECT": "#2ecc71",
    "GREAT": "#3498db",
    "GOOD": "#f1c40f",
    "MISS": "#e74c3c",
}

TEXT = "#ecf0f1"
TEXT_DIM = "#95a5a6"
SCORE = "#f39c12"

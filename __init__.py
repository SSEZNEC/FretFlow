"""Reusable UI widgets."""

from fretflow.ui.widgets.chord_diagram import ChordDiagramWidget
from fretflow.ui.widgets.fretboard_widget import FretboardWidget
from fretflow.ui.widgets.teacher_panel import TeacherPanel

try:
    from fretflow.ui.widgets.ghost_hand import GhostHandMode, GhostHandState
except ImportError:  # pragma: no cover
    GhostHandMode = None  # type: ignore
    GhostHandState = None  # type: ignore

__all__ = [
    "ChordDiagramWidget",
    "FretboardWidget",
    "GhostHandMode",
    "GhostHandState",
    "TeacherPanel",
]

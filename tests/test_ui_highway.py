"""Headless tests for the highway widget (no game logic assertions beyond wiring)."""

from __future__ import annotations

import os

import pytest

# Must be set before QApplication
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from fretflow.core.models import Note
from fretflow.ui.highway_widget import HighwayWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_highway_accepts_notes(qapp) -> None:
    w = HighwayWidget()
    notes = [
        Note(start_seconds=0.0, duration_seconds=0.3, midi_pitch=60),
        Note(start_seconds=0.5, duration_seconds=0.3, midi_pitch=64),
    ]
    w.set_notes(notes)
    w.set_song_time(0.0)
    w.set_hud(100, 3, "100%")
    w.mark_hit(60, 0.0, "PERFECT")
    # Smoke: paint without crash
    w.resize(640, 480)
    w.show()
    qapp.processEvents()
    w.close()


def test_game_window_builds(qapp) -> None:
    from fretflow.core.models import Measure, Note, Song, Track
    from fretflow.practice.settings import PracticeSettings
    from fretflow.ui.game_window import GameWindow

    notes = [Note(start_seconds=i * 0.5, duration_seconds=0.3, midi_pitch=60 + i) for i in range(4)]
    song = Song(
        title="UI Test",
        tracks=[Track(name="T", measures=[Measure(0, 0.0, 2.0, notes=notes)])],
        duration_seconds=2.0,
    )
    win = GameWindow(song=song, settings=PracticeSettings(song_id=song.id))
    win.show()
    qapp.processEvents()
    win.close()

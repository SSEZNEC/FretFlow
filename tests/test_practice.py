"""Tests for loop, metronome and practice settings."""

from __future__ import annotations

import pytest

from fretflow.practice.loop import LoopRegion
from fretflow.practice.metronome import Metronome
from fretflow.practice.settings import PracticeSettings
from uuid import uuid4


def test_loop_wrap() -> None:
    loop = LoopRegion(1.0, 3.0)
    assert loop.contains(1.5)
    assert not loop.contains(3.0)
    assert loop.should_wrap(3.0)
    assert loop.wrap_target() == 1.0


def test_loop_invalid() -> None:
    with pytest.raises(ValueError):
        LoopRegion(2.0, 1.0)


def test_metronome_beats() -> None:
    m = Metronome(bpm=120.0)  # 0.5 s per beat
    assert m.beat_interval_seconds == pytest.approx(0.5)
    assert m.beat_index_at(0.0) == 0
    assert m.beat_index_at(0.49) == 0
    assert m.beat_index_at(0.5) == 1
    assert m.next_beat_time(0.1) == pytest.approx(0.5)
    assert m.is_downbeat(0)
    assert m.is_downbeat(4)
    assert not m.is_downbeat(1)


def test_settings_validation() -> None:
    with pytest.raises(ValueError):
        PracticeSettings(song_id=uuid4(), tempo_factor=0.1)
    with pytest.raises(ValueError):
        PracticeSettings(song_id=uuid4(), section_start_seconds=2.0, section_end_seconds=1.0)

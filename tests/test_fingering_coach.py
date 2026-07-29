"""Tests for fingering engine, chords, fretboard and technique analysis."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fretflow.coach.skill_graph import SkillGraph
from fretflow.coach.skills import SkillId
from fretflow.coach.technique_detector import DifficultyLevel, TechniqueDetector
from fretflow.core.models import Measure, Note, Song, Technique, Track
from fretflow.practice.chord_analyser import ChordAnalyser
from fretflow.practice.fingering import FingeringEngine
from fretflow.practice.fretboard import (
    FretMarker,
    midi_to_preferred_position,
    note_to_position,
)


def test_midi_to_position_a4() -> None:
    # A4 = 69 → string 1 (high E=64) fret 5, or string 2 fret 10, etc.
    string, fret = midi_to_preferred_position(69)
    assert 1 <= string <= 6
    assert 0 <= fret <= 24


def test_fingering_assigns_fingers() -> None:
    notes = [
        Note(0.0, 0.4, 64, string=1, fret=0),   # open high E
        Note(0.5, 0.4, 65, string=1, fret=1),   # F
        Note(1.0, 0.4, 67, string=1, fret=3),   # G
    ]
    engine = FingeringEngine()
    assigned = engine.assign_sequence(notes)
    assert assigned[0].finger == 0  # open
    assert assigned[1].finger == 1
    assert assigned[2].finger in (1, 2, 3, 4)


def test_fingering_fills_missing_string_fret() -> None:
    notes = [Note(0.0, 0.3, 60), Note(0.5, 0.3, 62)]  # no string/fret
    assigned = FingeringEngine().assign_sequence(notes)
    assert all(n.string is not None and n.fret is not None for n in assigned)


def test_positions_at_time() -> None:
    notes = [
        Note(1.0, 0.3, 64, string=1, fret=0),
        Note(2.0, 0.3, 65, string=1, fret=1),
    ]
    engine = FingeringEngine()
    positions = engine.positions_at(notes, time_seconds=1.0, lookahead_seconds=1.5)
    markers = {p.marker for p in positions}
    assert FretMarker.CURRENT in markers
    assert FretMarker.NEXT in markers


def test_chord_analyser_c_major() -> None:
    # C E G
    notes = [
        Note(0.0, 0.5, 60, string=5, fret=3),
        Note(0.0, 0.5, 64, string=4, fret=2),
        Note(0.0, 0.5, 67, string=3, fret=0),
    ]
    voicings = ChordAnalyser().analyse(notes)
    assert len(voicings) == 1
    assert voicings[0].name.startswith("C")


def test_chord_power() -> None:
    notes = [
        Note(0.0, 0.4, 40, string=6, fret=0),  # E
        Note(0.0, 0.4, 47, string=5, fret=2),  # B
    ]
    voicings = ChordAnalyser().analyse(notes)
    assert len(voicings) == 1
    assert voicings[0].is_power_chord or "5" in voicings[0].name or "E" in voicings[0].name


def test_technique_detector_level() -> None:
    notes = [
        Note(i * 0.25, 0.2, 60 + (i % 5), string=4, fret=i % 5, technique=Technique.NONE)
        for i in range(20)
    ]
    song = Song(
        title="Test",
        tracks=[Track(name="G", measures=[Measure(0, 0.0, 5.0, notes=notes)])],
        duration_seconds=5.0,
    )
    pedagogy = TechniqueDetector().analyse(song)
    assert pedagogy.level in list(DifficultyLevel)
    assert pedagogy.estimated_minutes > 0


def test_technique_detector_bends() -> None:
    notes = [
        Note(0.0, 0.3, 64, string=1, fret=0, technique=Technique.BEND),
        Note(0.5, 0.3, 65, string=1, fret=1, technique=Technique.SLIDE),
    ]
    song = Song(
        title="Tech",
        tracks=[Track(name="G", measures=[Measure(0, 0.0, 1.0, notes=notes)])],
        duration_seconds=1.0,
    )
    pedagogy = TechniqueDetector().analyse(song)
    assert "bend" in pedagogy.stats.counts
    assert any("bend" in t.lower() for t in pedagogy.techniques_summary) or pedagogy.stats.counts.get("bend")


def test_skill_graph_prereqs() -> None:
    graph = SkillGraph()
    levels = {SkillId.PITCH_ACCURACY: 0.5, SkillId.RHYTHM_TIMING: 0.5}
    assert graph.prerequisites_met(SkillId.LEGATO, levels)
    assert not graph.prerequisites_met(SkillId.VIBRATO, {SkillId.BENDING: 0.1})


def test_note_to_position() -> None:
    n = Note(0.0, 0.2, 64, string=1, fret=0, finger=0)
    pos = note_to_position(n)
    assert pos.string == 1 and pos.fret == 0

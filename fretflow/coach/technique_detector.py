"""Detect techniques and pedagogical difficulty of a song."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

from fretflow.core.models import Note, Song, Technique
from fretflow.practice.chord_analyser import ChordAnalyser, ChordVoicing


class DifficultyLevel(str, Enum):
    BEGINNER = "debutant"
    ELEMENTARY = "elementaire"
    INTERMEDIATE = "intermediaire"
    ADVANCED = "avance"
    EXPERT = "expert"


@dataclass(slots=True)
class TechniqueStats:
    counts: dict[str, int] = field(default_factory=dict)
    power_chords: int = 0
    barre_candidates: int = 0  # fretted chords spanning 4+ strings same fret
    rapid_changes: int = 0     # successive notes < 150ms apart on different frets
    max_fret: int = 0
    unique_positions: int = 0


@dataclass(slots=True)
class SongPedagogy:
    """Pedagogical analysis produced at import time."""

    level: DifficultyLevel
    stats: TechniqueStats
    techniques_summary: list[str] = field(default_factory=list)
    chord_names: list[str] = field(default_factory=list)
    estimated_minutes: float = 0.0
    tips: list[str] = field(default_factory=list)


class TechniqueDetector:
    """Analyse a Song for techniques and difficulty (pure)."""

    def analyse(self, song: Song, track_index: int = 0) -> SongPedagogy:
        if not song.tracks:
            return SongPedagogy(
                level=DifficultyLevel.BEGINNER,
                stats=TechniqueStats(),
            )
        idx = min(track_index, len(song.tracks) - 1)
        notes = song.tracks[idx].notes
        stats = self._compute_stats(notes)
        chords = ChordAnalyser().analyse(notes)
        level = self._estimate_level(stats, chords)
        tips = self._tips(stats, chords, level)
        summary = [
            f"{count} {name}"
            for name, count in sorted(stats.counts.items(), key=lambda x: -x[1])
            if count > 0
        ]
        if stats.power_chords:
            summary.insert(0, f"{stats.power_chords} power chords")
        if stats.barre_candidates:
            summary.append(f"{stats.barre_candidates} barres potentiels")
        if stats.rapid_changes:
            summary.append(f"{stats.rapid_changes} changements rapides")

        chord_names = list(dict.fromkeys(c.name for c in chords))  # unique, ordered

        return SongPedagogy(
            level=level,
            stats=stats,
            techniques_summary=summary,
            chord_names=chord_names,
            estimated_minutes=max(1.0, song.duration_seconds / 60.0 * 1.5),
            tips=tips,
        )

    def _compute_stats(self, notes: list[Note]) -> TechniqueStats:
        counts: Counter[str] = Counter()
        max_fret = 0
        positions: set[tuple[int, int]] = set()
        rapid = 0

        for i, note in enumerate(notes):
            if note.technique is not Technique.NONE:
                counts[note.technique.name.lower()] += 1
            if note.fret is not None:
                max_fret = max(max_fret, note.fret)
                if note.string is not None:
                    positions.add((note.string, note.fret))
            if i > 0:
                prev = notes[i - 1]
                gap = note.start_seconds - prev.start_seconds
                if gap < 0.15 and note.fret is not None and prev.fret is not None:
                    if abs(note.fret - prev.fret) >= 3:
                        rapid += 1

        # Power chords / barres via chord analyser
        voicings = ChordAnalyser().analyse(notes)
        power = sum(1 for v in voicings if v.is_power_chord)
        barre = sum(
            1
            for v in voicings
            if len(v.notes) >= 4
            and len({n.fret for n in v.notes if n.fret and n.fret > 0}) == 1
        )

        return TechniqueStats(
            counts=dict(counts),
            power_chords=power,
            barre_candidates=barre,
            rapid_changes=rapid,
            max_fret=max_fret,
            unique_positions=len(positions),
        )

    def _estimate_level(
        self, stats: TechniqueStats, chords: list[ChordVoicing]
    ) -> DifficultyLevel:
        score = 0
        score += stats.max_fret // 3
        score += stats.barre_candidates * 2
        score += stats.rapid_changes // 5
        score += stats.counts.get("bend", 0)
        score += stats.counts.get("slide", 0) // 3
        score += len(chords) // 10
        if score <= 2:
            return DifficultyLevel.BEGINNER
        if score <= 5:
            return DifficultyLevel.ELEMENTARY
        if score <= 10:
            return DifficultyLevel.INTERMEDIATE
        if score <= 18:
            return DifficultyLevel.ADVANCED
        return DifficultyLevel.EXPERT

    def _tips(
        self,
        stats: TechniqueStats,
        chords: list[ChordVoicing],
        level: DifficultyLevel,
    ) -> list[str]:
        tips: list[str] = []
        if stats.barre_candidates:
            tips.append(
                f"Ce morceau contient {stats.barre_candidates} barré(s) potentiel(s). "
                "Travaillez-les isolément avant le tempo cible."
            )
        if stats.rapid_changes:
            tips.append(
                f"{stats.rapid_changes} changements de position rapides détectés. "
                "Utilisez le mode Learn pour les anticiper."
            )
        if stats.counts.get("bend", 0):
            tips.append("Des bends sont présents — vérifiez la justesse à l'oreille.")
        if level in (DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY):
            tips.append("Morçeau accessible — idéal pour consolider le rythme et les positions de base.")
        elif level is DifficultyLevel.EXPERT:
            tips.append("Niveau expert — fractionnez par sections de 4 mesures.")
        return tips

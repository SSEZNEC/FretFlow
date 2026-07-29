"""Skill graph — relationships between skills and techniques."""

from __future__ import annotations

from dataclasses import dataclass, field

from fretflow.coach.skills import SkillId
from fretflow.core.models import Technique


# Technique → skills it trains
TECHNIQUE_SKILLS: dict[Technique, list[SkillId]] = {
    Technique.BEND: [SkillId.BENDING, SkillId.PITCH_ACCURACY],
    Technique.VIBRATO: [SkillId.VIBRATO, SkillId.PITCH_ACCURACY],
    Technique.HAMMER_ON: [SkillId.LEGATO],
    Technique.PULL_OFF: [SkillId.LEGATO],
    Technique.SLIDE: [SkillId.LEGATO, SkillId.PITCH_ACCURACY],
    Technique.PALM_MUTE: [SkillId.RHYTHM_TIMING],
    Technique.TAP: [SkillId.LEGATO, SkillId.ALTERNATE_PICKING],
    Technique.HARMONIC: [SkillId.PITCH_ACCURACY],
    Technique.NONE: [SkillId.PITCH_ACCURACY, SkillId.RHYTHM_TIMING],
}


@dataclass(slots=True)
class SkillNode:
    skill_id: SkillId
    prerequisites: list[SkillId] = field(default_factory=list)
    related_techniques: list[Technique] = field(default_factory=list)


@dataclass(slots=True)
class SkillGraph:
    """Directed graph of skill dependencies (static knowledge)."""

    nodes: dict[SkillId, SkillNode] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.nodes:
            self.nodes = _default_graph()

    def skills_for_technique(self, technique: Technique) -> list[SkillId]:
        return list(TECHNIQUE_SKILLS.get(technique, [SkillId.PITCH_ACCURACY]))

    def prerequisites_met(
        self, skill_id: SkillId, levels: dict[SkillId, float], threshold: float = 0.4
    ) -> bool:
        node = self.nodes.get(skill_id)
        if node is None:
            return True
        return all(levels.get(p, 0.0) >= threshold for p in node.prerequisites)


def _default_graph() -> dict[SkillId, SkillNode]:
    return {
        SkillId.RHYTHM_TIMING: SkillNode(SkillId.RHYTHM_TIMING),
        SkillId.PITCH_ACCURACY: SkillNode(SkillId.PITCH_ACCURACY),
        SkillId.TEMPO_STABILITY: SkillNode(
            SkillId.TEMPO_STABILITY,
            prerequisites=[SkillId.RHYTHM_TIMING],
        ),
        SkillId.CHORD_CHANGES: SkillNode(
            SkillId.CHORD_CHANGES,
            prerequisites=[SkillId.PITCH_ACCURACY],
        ),
        SkillId.ALTERNATE_PICKING: SkillNode(
            SkillId.ALTERNATE_PICKING,
            prerequisites=[SkillId.RHYTHM_TIMING],
        ),
        SkillId.LEGATO: SkillNode(
            SkillId.LEGATO,
            prerequisites=[SkillId.PITCH_ACCURACY],
            related_techniques=[Technique.HAMMER_ON, Technique.PULL_OFF, Technique.SLIDE],
        ),
        SkillId.BENDING: SkillNode(
            SkillId.BENDING,
            prerequisites=[SkillId.PITCH_ACCURACY],
            related_techniques=[Technique.BEND],
        ),
        SkillId.VIBRATO: SkillNode(
            SkillId.VIBRATO,
            prerequisites=[SkillId.BENDING],
            related_techniques=[Technique.VIBRATO],
        ),
        SkillId.SIGHT_READING: SkillNode(
            SkillId.SIGHT_READING,
            prerequisites=[SkillId.RHYTHM_TIMING, SkillId.PITCH_ACCURACY],
        ),
        SkillId.SECTION_ENDURANCE: SkillNode(
            SkillId.SECTION_ENDURANCE,
            prerequisites=[SkillId.TEMPO_STABILITY],
        ),
    }

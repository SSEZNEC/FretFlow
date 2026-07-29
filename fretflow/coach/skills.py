"""Domain: skill taxonomy the coach tracks over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class SkillId(str, Enum):
    """Stable identifiers for skills (string enum for serialization)."""

    RHYTHM_TIMING = "rhythm_timing"
    PITCH_ACCURACY = "pitch_accuracy"
    TEMPO_STABILITY = "tempo_stability"
    CHORD_CHANGES = "chord_changes"
    ALTERNATE_PICKING = "alternate_picking"
    LEGATO = "legato"
    BENDING = "bending"
    VIBRATO = "vibrato"
    SIGHT_READING = "sight_reading"
    SECTION_ENDURANCE = "section_endurance"


SKILL_LABELS_FR: dict[SkillId, str] = {
    SkillId.RHYTHM_TIMING: "Precision rythmique",
    SkillId.PITCH_ACCURACY: "Justesse",
    SkillId.TEMPO_STABILITY: "Stabilite du tempo",
    SkillId.CHORD_CHANGES: "Changements d'accords",
    SkillId.ALTERNATE_PICKING: "Alternate picking",
    SkillId.LEGATO: "Legato (hammer / pull-off)",
    SkillId.BENDING: "Bends",
    SkillId.VIBRATO: "Vibrato",
    SkillId.SIGHT_READING: "Lecture a vue",
    SkillId.SECTION_ENDURANCE: "Endurance de section",
}


@dataclass(slots=True)
class SkillLevel:
    """Estimated mastery of one skill in [0, 1]."""

    skill_id: SkillId
    level: float = 0.0
    sample_count: int = 0
    last_session_id: UUID | None = None

    def __post_init__(self) -> None:
        self.level = max(0.0, min(1.0, self.level))

    @property
    def label_fr(self) -> str:
        return SKILL_LABELS_FR.get(self.skill_id, self.skill_id.value)

    def update(self, observation: float, weight: float = 1.0) -> None:
        """Exponential moving average toward observation in [0, 1]."""
        observation = max(0.0, min(1.0, observation))
        weight = max(0.0, min(1.0, weight))
        if self.sample_count == 0:
            self.level = observation
        else:
            alpha = 0.3 * weight
            self.level = (1 - alpha) * self.level + alpha * observation
        self.sample_count += 1


@dataclass(slots=True)
class SkillProfile:
    """All tracked skills for a player."""

    levels: dict[SkillId, SkillLevel] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)

    def get(self, skill_id: SkillId) -> SkillLevel:
        if skill_id not in self.levels:
            self.levels[skill_id] = SkillLevel(skill_id=skill_id)
        return self.levels[skill_id]

    def weakest(self, n: int = 3, min_samples: int = 1) -> list[SkillLevel]:
        candidates = [s for s in self.levels.values() if s.sample_count >= min_samples]
        candidates.sort(key=lambda s: s.level)
        return candidates[:n]

    def strongest(self, n: int = 3, min_samples: int = 1) -> list[SkillLevel]:
        candidates = [s for s in self.levels.values() if s.sample_count >= min_samples]
        candidates.sort(key=lambda s: s.level, reverse=True)
        return candidates[:n]

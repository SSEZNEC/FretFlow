"""Automatic practice session plans (warm-up → work → cool-down)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import UUID, uuid4

from fretflow.practice.exercise import Exercise, ExerciseKind
from fretflow.practice.exercise_plan import ExercisePlan, PlanStatus


class BlockKind(Enum):
    WARMUP = auto()
    CHORDS = auto()
    SONG = auto()
    TECHNIQUE = auto()
    COOLDOWN = auto()


@dataclass(slots=True)
class PlanBlock:
    kind: BlockKind
    title: str
    minutes: float
    exercise: Exercise | None = None
    description: str = ""


@dataclass(slots=True)
class TrainingPlan:
    """A full structured practice session."""

    title: str
    blocks: list[PlanBlock] = field(default_factory=list)
    song_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    @property
    def total_minutes(self) -> float:
        return sum(b.minutes for b in self.blocks)

    def to_exercise_plan(self) -> ExercisePlan:
        plan = ExercisePlan(
            title=self.title,
            status=PlanStatus.ACTIVE,
            goal_summary=f"Séance structurée — {self.total_minutes:.0f} min",
            estimated_minutes=self.total_minutes,
        )
        for block in self.blocks:
            if block.exercise is not None:
                plan.add(block.exercise)
        return plan


@dataclass(slots=True)
class TrainingPlanBuilder:
    """Builds balanced sessions from available time budget."""

    def build(
        self,
        total_minutes: float = 45.0,
        song_id: UUID | None = None,
        song_title: str = "Morceau",
        focus_technique: str | None = None,
    ) -> TrainingPlan:
        total_minutes = max(15.0, min(total_minutes, 120.0))
        # Proportions
        warmup = max(3.0, total_minutes * 0.10)
        chords = total_minutes * 0.20
        song = total_minutes * 0.40
        technique = total_minutes * 0.20
        cooldown = max(3.0, total_minutes * 0.10)
        # Normalize residual
        s = warmup + chords + song + technique + cooldown
        scale = total_minutes / s
        warmup, chords, song, technique, cooldown = (
            warmup * scale, chords * scale, song * scale, technique * scale, cooldown * scale
        )

        tech_label = focus_technique or "précision & rythme"
        blocks = [
            PlanBlock(
                BlockKind.WARMUP,
                "Échauffement",
                warmup,
                Exercise(
                    title="Échauffement cordes à vide / chromatismes",
                    kind=ExerciseKind.TECHNIQUE_DRILL,
                    tempo_factor=0.6,
                    instructions="Jouez lentement, détendez les épaules, écoutez chaque note.",
                    technique_tags=["warmup"],
                ),
                description="Assouplir les doigts et l'oreille.",
            ),
            PlanBlock(
                BlockKind.CHORDS,
                "Accords",
                chords,
                Exercise(
                    title="Enchaînements d'accords",
                    kind=ExerciseKind.TECHNIQUE_DRILL,
                    tempo_factor=0.7,
                    instructions="Changements lents puis fluides. Relâchez la pression entre les accords.",
                    technique_tags=["chords"],
                ),
                description="Fluidité des changements.",
            ),
            PlanBlock(
                BlockKind.SONG,
                f"Morceau — {song_title}",
                song,
                Exercise(
                    title=f"Travail du morceau : {song_title}",
                    kind=ExerciseKind.SECTION_LOOP,
                    song_id=song_id,
                    tempo_factor=0.75,
                    target_repetitions=3,
                    instructions="Bouclez les passages difficiles avant une passe complète.",
                ),
                description="Application musicale.",
            ),
            PlanBlock(
                BlockKind.TECHNIQUE,
                f"Technique — {tech_label}",
                technique,
                Exercise(
                    title=f"Focus : {tech_label}",
                    kind=ExerciseKind.TECHNIQUE_DRILL,
                    tempo_factor=0.65,
                    instructions="Qualité avant vitesse. 4 répétitions propres valent mieux que 20 approximatives.",
                    technique_tags=[focus_technique or "accuracy"],
                ),
                description="Consolider un point faible.",
            ),
            PlanBlock(
                BlockKind.COOLDOWN,
                "Retour au calme",
                cooldown,
                Exercise(
                    title="Improvisation douce / accords ouverts",
                    kind=ExerciseKind.CUSTOM,
                    tempo_factor=0.5,
                    instructions="Jouez librement, sans pression. Notez ce qui s'est bien passé.",
                    technique_tags=["cooldown"],
                ),
                description="Ancrer les acquis.",
            ),
        ]
        return TrainingPlan(
            title=f"Séance {total_minutes:.0f} min — {song_title}",
            blocks=blocks,
            song_id=song_id,
        )

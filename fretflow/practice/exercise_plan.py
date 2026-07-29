"""Domain: ordered plan of exercises for a practice session."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from uuid import UUID, uuid4

from fretflow.practice.exercise import Exercise


class PlanStatus(Enum):
    DRAFT = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    ABANDONED = auto()


@dataclass(slots=True)
class ExercisePlan:
    """A sequence of exercises with an optional time budget.

    Pedagogical structure only — scheduling lives in profile/coach consumers.
    """

    title: str
    exercises: list[Exercise] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    goal_summary: str = ""
    estimated_minutes: float | None = None
    id: UUID = field(default_factory=uuid4)

    def add(self, exercise: Exercise) -> None:
        self.exercises.append(exercise)

    def next_exercise(self, completed_ids: set[UUID]) -> Exercise | None:
        for ex in self.exercises:
            if ex.id not in completed_ids:
                return ex
        return None

    @property
    def exercise_count(self) -> int:
        return len(self.exercises)

    def progress_ratio(self, completed_ids: set[UUID]) -> float:
        if not self.exercises:
            return 1.0
        done = sum(1 for ex in self.exercises if ex.id in completed_ids)
        return done / len(self.exercises)

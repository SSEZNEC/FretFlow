"""Simple daily / weekly practice goals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, auto
from uuid import UUID, uuid4


class GoalPeriod(Enum):
    DAILY = auto()
    WEEKLY = auto()


class GoalKind(Enum):
    PRACTICE_MINUTES = auto()
    SESSION_COUNT = auto()
    ACCURACY_TARGET = auto()
    EXERCISE_COMPLETIONS = auto()


@dataclass(slots=True)
class Goal:
    """A measurable practice target."""

    kind: GoalKind
    period: GoalPeriod
    target_value: float
    current_value: float = 0.0
    label: str = ""
    id: UUID = field(default_factory=uuid4)
    active: bool = True

    def __post_init__(self) -> None:
        if self.target_value <= 0:
            raise ValueError("target_value must be > 0")
        if not self.label:
            self.label = _default_label(self.kind, self.period, self.target_value)

    @property
    def progress_ratio(self) -> float:
        return min(1.0, self.current_value / self.target_value)

    @property
    def is_completed(self) -> bool:
        return self.current_value >= self.target_value

    def record(self, amount: float) -> None:
        self.current_value = max(0.0, self.current_value + amount)


def _default_label(kind: GoalKind, period: GoalPeriod, target: float) -> str:
    period_fr = "quotidien" if period is GoalPeriod.DAILY else "hebdomadaire"
    if kind is GoalKind.PRACTICE_MINUTES:
        return f"Objectif {period_fr} : {target:.0f} min de pratique"
    if kind is GoalKind.SESSION_COUNT:
        return f"Objectif {period_fr} : {target:.0f} seance(s)"
    if kind is GoalKind.ACCURACY_TARGET:
        return f"Atteindre {target:.0%} de precision"
    if kind is GoalKind.EXERCISE_COMPLETIONS:
        return f"Terminer {target:.0f} exercice(s)"
    return f"Objectif {period_fr}"


def default_daily_goals() -> list[Goal]:
    return [
        Goal(kind=GoalKind.PRACTICE_MINUTES, period=GoalPeriod.DAILY, target_value=15.0),
        Goal(kind=GoalKind.SESSION_COUNT, period=GoalPeriod.DAILY, target_value=1.0),
    ]


def default_weekly_goals() -> list[Goal]:
    return [
        Goal(kind=GoalKind.PRACTICE_MINUTES, period=GoalPeriod.WEEKLY, target_value=90.0),
        Goal(kind=GoalKind.SESSION_COUNT, period=GoalPeriod.WEEKLY, target_value=5.0),
    ]


@dataclass(slots=True)
class GoalTracker:
    """In-memory goal tracker for the current day / week."""

    daily: list[Goal] = field(default_factory=default_daily_goals)
    weekly: list[Goal] = field(default_factory=default_weekly_goals)
    today: date = field(default_factory=date.today)

    def record_session(self, duration_seconds: float, accuracy: float) -> None:
        minutes = duration_seconds / 60.0
        for goal in self.daily + self.weekly:
            if not goal.active:
                continue
            if goal.kind is GoalKind.PRACTICE_MINUTES:
                goal.record(minutes)
            elif goal.kind is GoalKind.SESSION_COUNT:
                goal.record(1.0)
            elif goal.kind is GoalKind.ACCURACY_TARGET:
                if accuracy >= goal.target_value:
                    goal.current_value = goal.target_value

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        for goal in self.daily + self.weekly:
            mark = "OK" if goal.is_completed else f"{goal.progress_ratio:.0%}"
            lines.append(f"[{mark}] {goal.label} ({goal.current_value:.1f}/{goal.target_value:.0f})")
        return lines

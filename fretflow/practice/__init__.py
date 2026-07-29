"""Practice tools: exercises, plans, loops, metronome."""

from fretflow.practice.exercise import Exercise, ExerciseKind
from fretflow.practice.exercise_plan import ExercisePlan, PlanStatus
from fretflow.practice.loop import LoopRegion
from fretflow.practice.metronome import Metronome
from fretflow.practice.session_report import (
    NoteOutcome,
    SectionDifficulty,
    SectionStats,
    SessionReport,
    build_sections_from_outcomes,
)
from fretflow.practice.settings import PracticeSettings

__all__ = [
    "Exercise",
    "ExerciseKind",
    "ExercisePlan",
    "PlanStatus",
    "LoopRegion",
    "Metronome",
    "NoteOutcome",
    "SectionDifficulty",
    "SectionStats",
    "SessionReport",
    "build_sections_from_outcomes",
    "PracticeSettings",
]


def __getattr__(name: str):
    if name == "report_from_runner":
        from fretflow.practice.report_builder import report_from_runner
        return report_from_runner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

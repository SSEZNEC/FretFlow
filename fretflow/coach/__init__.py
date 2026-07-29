"""Session analysis, recommendations and skill tracking."""

from fretflow.coach.goals import Goal, GoalKind, GoalPeriod, GoalTracker
from fretflow.coach.recommendation_engine import Recommendation, RecommendationEngine
from fretflow.coach.skill_graph import SkillGraph, TECHNIQUE_SKILLS
from fretflow.coach.skills import SKILL_LABELS_FR, SkillId, SkillLevel, SkillProfile
from fretflow.coach.technique_detector import (
    DifficultyLevel,
    SongPedagogy,
    TechniqueDetector,
    TechniqueStats,
)
from fretflow.coach.weakness_detector import Weakness, WeaknessKind, detect_weaknesses

__all__ = [
    "CoachResult",
    "CoachService",
    "DifficultyLevel",
    "Goal",
    "GoalKind",
    "GoalPeriod",
    "GoalTracker",
    "Recommendation",
    "RecommendationEngine",
    "SKILL_LABELS_FR",
    "SkillGraph",
    "SkillId",
    "SkillLevel",
    "SkillProfile",
    "SongPedagogy",
    "TECHNIQUE_SKILLS",
    "TechniqueDetector",
    "TechniqueStats",
    "Weakness",
    "WeaknessKind",
    "detect_weaknesses",
]


def __getattr__(name: str):
    if name in ("CoachService", "CoachResult"):
        from fretflow.coach.service import CoachResult, CoachService
        return CoachService if name == "CoachService" else CoachResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

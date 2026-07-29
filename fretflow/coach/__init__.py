"""Session analysis, recommendations and skill tracking."""

from fretflow.coach.goals import Goal, GoalKind, GoalPeriod, GoalTracker
from fretflow.coach.recommendation_engine import Recommendation, RecommendationEngine
from fretflow.coach.skills import SKILL_LABELS_FR, SkillId, SkillLevel, SkillProfile
from fretflow.coach.weakness_detector import Weakness, WeaknessKind, detect_weaknesses

__all__ = [
    "CoachResult",
    "CoachService",
    "Goal",
    "GoalKind",
    "GoalPeriod",
    "GoalTracker",
    "Recommendation",
    "RecommendationEngine",
    "SKILL_LABELS_FR",
    "SkillId",
    "SkillLevel",
    "SkillProfile",
    "Weakness",
    "WeaknessKind",
    "detect_weaknesses",
]


def __getattr__(name: str):
    if name in ("CoachService", "CoachResult"):
        from fretflow.coach.service import CoachResult, CoachService
        return CoachService if name == "CoachService" else CoachResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

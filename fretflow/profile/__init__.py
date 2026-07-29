"""User profiles, goals, sessions and statistics."""

from fretflow.profile.repository import ProfileRepository, SessionRepository

__all__ = ["ProfileRepository", "SessionRepository", "SkillStore"]


def __getattr__(name: str):
    if name == "SkillStore":
        from fretflow.profile.skills_store import SkillStore
        return SkillStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

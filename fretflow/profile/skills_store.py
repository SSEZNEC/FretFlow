"""Persist SkillProfile in SQLite (local-first)."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from uuid import UUID

from fretflow.coach.skills import SkillId, SkillLevel, SkillProfile
from fretflow.core.errors import PersistenceError
from fretflow.library.db import connect

logger = logging.getLogger("fretflow.profile.skills_store")

SKILLS_SQL = """
CREATE TABLE IF NOT EXISTS skill_profiles (
    id TEXT PRIMARY KEY,
    levels_json TEXT NOT NULL DEFAULT '{}',
    updated_at REAL NOT NULL
);
"""


class SkillStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path
        with connect(db_path) as conn:
            conn.executescript(SKILLS_SQL)
            conn.commit()

    def load(self, profile_id: UUID | str | None = None) -> SkillProfile:
        with connect(self._db_path) as conn:
            if profile_id is None:
                row = conn.execute(
                    "SELECT * FROM skill_profiles ORDER BY updated_at DESC LIMIT 1"
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM skill_profiles WHERE id = ?", (str(profile_id),)
                ).fetchone()
            if row is None:
                return SkillProfile()
            data = json.loads(row["levels_json"])
            profile = SkillProfile(id=UUID(row["id"]))
            for key, val in data.items():
                try:
                    sid = SkillId(key)
                except ValueError:
                    continue
                profile.levels[sid] = SkillLevel(
                    skill_id=sid,
                    level=float(val.get("level", 0)),
                    sample_count=int(val.get("sample_count", 0)),
                )
            return profile

    def save(self, profile: SkillProfile) -> None:
        import time

        payload = {
            sid.value: {"level": sl.level, "sample_count": sl.sample_count}
            for sid, sl in profile.levels.items()
        }
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO skill_profiles (id, levels_json, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        levels_json = excluded.levels_json,
                        updated_at = excluded.updated_at
                    """,
                    (str(profile.id), json.dumps(payload), time.time()),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise PersistenceError(f"Cannot save skill profile: {exc}") from exc
        logger.info("Saved skill profile %s (%d skills)", profile.id, len(profile.levels))

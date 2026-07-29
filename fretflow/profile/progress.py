"""Progress aggregates for the dashboard (read-only over sessions)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import UUID

from fretflow.library.db import connect
from fretflow.profile.repository import ensure_session_tables


@dataclass(slots=True)
class DayStats:
    day: date
    session_count: int = 0
    total_minutes: float = 0.0
    average_accuracy: float = 0.0
    total_score: int = 0


@dataclass(slots=True)
class ProgressSummary:
    total_sessions: int = 0
    total_minutes: float = 0.0
    average_accuracy: float = 0.0
    best_score: int = 0
    last_session_at: float | None = None
    days: list[DayStats] = field(default_factory=list)
    recent_sessions: list[dict] = field(default_factory=list)


class ProgressService:
    """Compute dashboard stats from the sessions table."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path
        ensure_session_tables(db_path)

    def summary(self, days: int = 30) -> ProgressSummary:
        since = datetime.now().timestamp() - days * 86400
        with connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM sessions
                WHERE started_at >= ?
                ORDER BY started_at DESC
                """,
                (since,),
            ).fetchall()
            all_rows = [dict(r) for r in rows]

            totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS n,
                    COALESCE(SUM(duration_seconds), 0) AS dur,
                    COALESCE(AVG(
                        CASE WHEN notes_hit + notes_missed > 0
                        THEN CAST(notes_hit AS REAL) / (notes_hit + notes_missed)
                        ELSE NULL END
                    ), 0) AS acc,
                    COALESCE(MAX(score), 0) AS best,
                    MAX(started_at) AS last_at
                FROM sessions
                """
            ).fetchone()

        by_day: dict[date, list[dict]] = {}
        for r in all_rows:
            d = datetime.fromtimestamp(r["started_at"]).date()
            by_day.setdefault(d, []).append(r)

        day_stats: list[DayStats] = []
        for d in sorted(by_day.keys()):
            sessions = by_day[d]
            accuracies = []
            minutes = 0.0
            score_sum = 0
            for s in sessions:
                total = s["notes_hit"] + s["notes_missed"]
                if total > 0:
                    accuracies.append(s["notes_hit"] / total)
                minutes += float(s["duration_seconds"]) / 60.0
                score_sum += int(s["score"])
            day_stats.append(
                DayStats(
                    day=d,
                    session_count=len(sessions),
                    total_minutes=minutes,
                    average_accuracy=(sum(accuracies) / len(accuracies)) if accuracies else 0.0,
                    total_score=score_sum,
                )
            )

        return ProgressSummary(
            total_sessions=int(totals["n"] or 0),
            total_minutes=float(totals["dur"] or 0) / 60.0,
            average_accuracy=float(totals["acc"] or 0),
            best_score=int(totals["best"] or 0),
            last_session_at=totals["last_at"],
            days=day_stats,
            recent_sessions=all_rows[:15],
        )

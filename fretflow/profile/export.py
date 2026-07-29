"""Export practice statistics to CSV / JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from fretflow.profile.progress import ProgressService


def export_sessions_json(path: Path, db_path: Path | None = None, days: int = 365) -> Path:
    summary = ProgressService(db_path).summary(days=days)
    payload = {
        "total_sessions": summary.total_sessions,
        "total_minutes": summary.total_minutes,
        "average_accuracy": summary.average_accuracy,
        "best_score": summary.best_score,
        "sessions": summary.recent_sessions,
        "days": [
            {
                "day": d.day.isoformat(),
                "session_count": d.session_count,
                "total_minutes": d.total_minutes,
                "average_accuracy": d.average_accuracy,
                "total_score": d.total_score,
            }
            for d in summary.days
        ],
    }
    path = Path(path)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def export_sessions_csv(path: Path, db_path: Path | None = None, days: int = 365) -> Path:
    summary = ProgressService(db_path).summary(days=days)
    path = Path(path)
    fieldnames = [
        "id", "song_id", "started_at", "duration_seconds",
        "notes_hit", "notes_missed", "notes_expected",
        "score", "max_combo", "tempo_factor",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in summary.recent_sessions:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return path

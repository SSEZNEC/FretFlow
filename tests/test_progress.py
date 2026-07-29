"""Tests for progress dashboard and export."""

from __future__ import annotations

import json

import pytest
from pathlib import Path
from uuid import uuid4

from fretflow.core.models import Session
from fretflow.profile.export import export_sessions_csv, export_sessions_json
from fretflow.profile.progress import ProgressService
from fretflow.profile.repository import SessionRepository


def test_progress_summary(tmp_path: Path) -> None:
    db = tmp_path / "lib.db"
    repo = SessionRepository(db_path=db)
    for i in range(3):
        repo.save(
            Session(
                song_id=uuid4(),
                started_at=1_700_000_000.0 + i * 100,
                duration_seconds=120.0,
                notes_hit=8,
                notes_missed=2,
                notes_expected=10,
                score=500 + i,
            )
        )
    summary = ProgressService(db_path=db).summary(days=3650)
    assert summary.total_sessions == 3
    assert summary.average_accuracy == pytest.approx(0.8)
    assert summary.best_score == 502
    assert summary.total_minutes == pytest.approx(6.0)


def test_export_json_csv(tmp_path: Path) -> None:
    import pytest
    db = tmp_path / "lib.db"
    repo = SessionRepository(db_path=db)
    repo.save(
        Session(
            song_id=uuid4(),
            started_at=1_700_000_000.0,
            duration_seconds=60.0,
            notes_hit=5,
            notes_missed=0,
            notes_expected=5,
            score=100,
        )
    )
    # ProgressService uses default db unless we pass db_path
    jpath = tmp_path / "out.json"
    # export uses ProgressService() without db - need to pass
    # Update: export functions accept db_path
    export_sessions_json(jpath, db_path=db, days=3650)
    data = json.loads(jpath.read_text())
    assert data["total_sessions"] >= 1

    cpath = tmp_path / "out.csv"
    export_sessions_csv(cpath, db_path=db, days=3650)
    assert cpath.read_text().startswith("id,")

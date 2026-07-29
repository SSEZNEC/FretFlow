"""Game / practice window — wires SessionRunner to the highway widget."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from fretflow.core.config import AppConfig, load_config
from fretflow.core.models import Song
from fretflow.engine import PlayedNoteEvent, SessionRunner
from fretflow.input.keyboard import key_to_midi
from fretflow.practice.settings import PracticeSettings
from fretflow.profile import SessionRepository
from fretflow.ui.highway_widget import HighwayWidget

logger = logging.getLogger("fretflow.ui.game_window")


class GameWindow(QMainWindow):
    """Playable practice session with on-screen highway."""

    def __init__(
        self,
        song: Song,
        settings: PracticeSettings | None = None,
        config: AppConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"FretFlow — {song.title}")
        self.resize(720, 640)

        self._config = config or load_config()
        self._settings = settings or PracticeSettings(song_id=song.id)
        self._runner = SessionRunner(
            song=song,
            settings=self._settings,
            windows=self._config.judgment,
        )
        self._finished = False

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._highway = HighwayWidget()
        track = song.tracks[self._settings.track_index] if song.tracks else None
        notes = track.notes if track else []
        start = self._settings.section_start_seconds or 0.0
        end = self._settings.section_end_seconds
        if start or end is not None:
            notes = [
                n
                for n in notes
                if n.start_seconds >= start and (end is None or n.start_seconds < end)
            ]
        self._highway.set_notes(notes)
        self._highway.key_pressed.connect(self._on_key)
        layout.addWidget(self._highway, stretch=1)

        # Controls
        controls = QHBoxLayout()
        self._btn_play = QPushButton("▶ Lecture")
        self._btn_play.clicked.connect(self._toggle_play)
        controls.addWidget(self._btn_play)

        controls.addWidget(QLabel("Tempo"))
        self._tempo_slider = QSlider(Qt.Orientation.Horizontal)
        self._tempo_slider.setRange(50, 100)
        self._tempo_slider.setValue(int(self._settings.tempo_factor * 100))
        self._tempo_slider.valueChanged.connect(self._on_tempo)
        controls.addWidget(self._tempo_slider)
        self._tempo_label = QLabel(f"{self._settings.tempo_factor:.0%}")
        controls.addWidget(self._tempo_label)

        self._status = QLabel("Espace : play/pause  ·  A–K : notes")
        controls.addWidget(self._status, stretch=1)
        layout.addLayout(controls)

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._on_frame)

        self._update_hud()

    def _toggle_play(self) -> None:
        if self._runner.clock.is_running:
            self._runner.pause()
            self._timer.stop()
            self._btn_play.setText("▶ Lecture")
        else:
            if self._finished:
                return
            self._runner.start()
            self._timer.start()
            self._btn_play.setText("⏸ Pause")
            self._highway.setFocus()

    def _on_tempo(self, value: int) -> None:
        factor = value / 100.0
        self._runner.clock.set_tempo_factor(factor)
        self._tempo_label.setText(f"{factor:.0%}")

    def _on_key(self, key: str) -> None:
        if key == " ":
            self._toggle_play()
            return
        midi = key_to_midi(key)
        if midi is None:
            return
        if not self._runner.clock.is_running:
            return
        t = self._runner.clock.current_time()
        hit = self._runner.handle_played_note(
            PlayedNoteEvent(midi_pitch=midi, time_seconds=t)
        )
        if hit:
            self._highway.mark_hit(hit.midi_pitch, hit.expected_seconds, hit.judgment.name)
            self._update_hud()

    def _on_frame(self) -> None:
        t = self._runner.clock.current_time()
        self._highway.set_song_time(t)
        misses = self._runner.tick()
        if misses:
            self._update_hud()
        if self._runner.clock.is_finished or self._runner.progress >= 1.0:
            self._finish()

    def _update_hud(self) -> None:
        report = self._runner.build_report()
        acc = f"{report.accuracy:.0%}" if (report.notes_hit + report.notes_missed) else "—"
        self._highway.set_hud(report.score, self._runner._combo, acc)

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        self._timer.stop()
        self._runner.pause()
        self._btn_play.setText("Terminé")
        self._btn_play.setEnabled(False)

        report = self._runner.build_report()
        session = self._runner.build_session()
        try:
            SessionRepository().save(session)
        except Exception:
            logger.exception("Failed to save session")

        lines = [
            f"Score : {report.score}",
            f"Précision : {report.accuracy:.0%}",
            f"Hits / Miss : {report.notes_hit} / {report.notes_missed}",
            f"Max combo : {report.max_combo}",
            "",
            *report.recommendations,
        ]
        QMessageBox.information(self, "Rapport de session", "\n".join(lines))

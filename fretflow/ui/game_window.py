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
from fretflow.audio.reference_audio import ReferenceAudioEngine, ReferenceMode
from fretflow.audio.sample_player import NullSink
from fretflow.practice.chord_analyser import ChordAnalyser
from fretflow.practice.fingering import FingeringEngine
from fretflow.ui.highway_widget import HighwayWidget
from fretflow.coach.teacher_tips import TeacherTipEngine
from fretflow.ui.widgets.chord_diagram import ChordDiagramWidget
from fretflow.ui.widgets.fretboard_widget import FretboardWidget
from fretflow.ui.widgets.teacher_panel import TeacherPanel

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
        self.resize(1000, 720)

        self._config = config or load_config()
        self._settings = settings or PracticeSettings(song_id=song.id)
        self._runner = SessionRunner(
            song=song,
            settings=self._settings,
            windows=self._config.judgment,
        )
        self._finished = False
        self._fingering = FingeringEngine()
        self._chord_analyser = ChordAnalyser()
        track = song.tracks[self._settings.track_index] if song.tracks else None
        raw_notes = track.notes if track else []
        self._all_notes = self._fingering.assign_sequence(raw_notes)
        self._chords = self._chord_analyser.analyse(self._all_notes)
        self._ref_audio = ReferenceAudioEngine(
            mode=ReferenceMode.LEARN if self._settings.learn_mode else ReferenceMode.NOTE,
            sink=NullSink(),  # UI can swap to default_sink() when audio desired
        )
        self._ref_note_idx = 0
        self._tip_engine = TeacherTipEngine()
        self._last_hit: bool | None = None
        self._last_offset_ms: float | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        left = QVBoxLayout()
        root.addLayout(left, stretch=3)

        self._teacher = TeacherPanel()
        root.addWidget(self._teacher, stretch=1)

        layout = left  # existing code appends to layout

        self._highway = HighwayWidget()
        notes = list(self._all_notes)
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

        fret_row = QHBoxLayout()
        self._fretboard = FretboardWidget(frets=15)
        fret_row.addWidget(self._fretboard, stretch=1)
        self._chord_diagram = ChordDiagramWidget()
        fret_row.addWidget(self._chord_diagram)
        layout.addLayout(fret_row)

        # Controls
        controls = QHBoxLayout()
        self._btn_play = QPushButton("▶ Lecture")
        self._btn_play.clicked.connect(self._toggle_play)
        controls.addWidget(self._btn_play)

        self._btn_learn = QPushButton("Mode Learn")
        self._btn_learn.setCheckable(True)
        self._btn_learn.toggled.connect(self._toggle_learn)
        controls.addWidget(self._btn_learn)

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


    def _toggle_learn(self, enabled: bool) -> None:
        """Learn mode: slow tempo and emphasize next positions."""
        if enabled:
            self._settings.tempo_factor = min(self._settings.tempo_factor, 0.6)
            self._tempo_slider.setValue(int(self._settings.tempo_factor * 100))
            self._runner.clock.set_tempo_factor(self._settings.tempo_factor)
            self._ref_audio.set_mode(ReferenceMode.LEARN)
            self._status.setText("Mode Learn — tempo réduit, anticipez les positions")
        else:
            self._ref_audio.set_mode(ReferenceMode.NOTE)
            self._status.setText("")
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
            self._last_hit = True
            self._last_offset_ms = hit.offset_ms
            self._highway.mark_hit(hit.midi_pitch, hit.expected_seconds, hit.judgment.name)
            self._update_hud()
        else:
            self._last_hit = False

    def _on_frame(self) -> None:
        t = self._runner.clock.current_time()
        self._highway.set_song_time(t)
        self._update_fretboard()
        misses = self._runner.tick()
        if misses:
            self._update_hud()
        if self._runner.clock.is_finished or self._runner.progress >= 1.0:
            self._finish()

    def _update_hud(self) -> None:
        report = self._runner.build_report()
        acc = f"{report.accuracy:.0%}" if (report.notes_hit + report.notes_missed) else "—"
        self._highway.set_hud(report.score, self._runner._combo, acc)


    def _update_fretboard(self) -> None:
        t = self._runner.clock.song_time_seconds
        # Reference audio: play notes as they approach
        for note in self._all_notes:
            if 0 <= note.start_seconds - t <= 0.05:
                self._ref_audio.on_note_approaching(note)
        positions = self._fingering.positions_at(self._all_notes, t)
        chord_name = None
        for ch in self._chords:
            if abs(ch.start_seconds - t) < 0.12:
                chord_name = ch.name
                self._chord_diagram.set_chord(ch.name, list(ch.positions))
                break
        else:
            if not positions:
                self._chord_diagram.clear()

        info = ""
        current = [p for p in positions if p.marker.name == "CURRENT"]
        if current:
            p = current[0]
            finger_txt = f"doigt {p.finger}" if p.finger else "corde a vide"
            info = f"Corde {p.string}  case {p.fret}  {finger_txt}"
            if p.midi_pitch is not None:
                names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
                info = f"{names[p.midi_pitch % 12]}  ·  {info}"
        self._fretboard.set_positions(positions, chord_name=chord_name, info=info)
        tips = self._tip_engine.tips_at(
            t, self._all_notes, positions,
            last_hit=self._last_hit,
            last_offset_ms=self._last_offset_ms,
            combo=getattr(self._runner, "_combo", 0),
        )
        if tips:
            self._teacher.show_tips(tips)

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

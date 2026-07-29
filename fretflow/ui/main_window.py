"""Main window: library list + launch practice."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fretflow.importers import import_song
from fretflow.library import LibraryScanner, SongRepository
from fretflow.practice.settings import PracticeSettings
from fretflow.ui.dashboard_window import DashboardWindow
from fretflow.ui.game_window import GameWindow

logger = logging.getLogger("fretflow.ui.main_window")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FretFlow")
        self.resize(640, 480)

        self._repo = SongRepository()
        self._game: GameWindow | None = None
        self._dashboard: DashboardWindow | None = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel("<h2>FretFlow — Bibliothèque</h2>"))

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._play_selected)
        layout.addWidget(self._list, stretch=1)

        buttons = QHBoxLayout()
        btn_scan = QPushButton("Scanner un dossier…")
        btn_scan.clicked.connect(self._scan)
        buttons.addWidget(btn_scan)

        btn_import = QPushButton("Importer un fichier…")
        btn_import.clicked.connect(self._import_file)
        buttons.addWidget(btn_import)

        btn_demo = QPushButton("Démo C majeur")
        btn_demo.clicked.connect(self._play_demo)
        buttons.addWidget(btn_demo)

        btn_play = QPushButton("Jouer")
        btn_play.clicked.connect(self._play_selected)
        buttons.addWidget(btn_play)

        btn_progress = QPushButton("Tableau de bord")
        btn_progress.clicked.connect(self._open_dashboard)
        buttons.addWidget(btn_progress)

        layout.addLayout(buttons)
        self._refresh()

    def _refresh(self) -> None:
        self._list.clear()
        for s in self._repo.list_songs():
            label = f"{s['title']}  —  {s['artist']}  ({s['tempo_bpm']:.0f} BPM, {float(s['duration_seconds']):.0f}s)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, s["source_path"])
            self._list.addItem(item)

    def _scan(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Dossier de partitions")
        if not path:
            return
        result = LibraryScanner(repository=self._repo).scan([Path(path)])
        QMessageBox.information(
            self,
            "Scan terminé",
            f"Importés : {result.imported}\nIgnorés : {result.skipped}\nÉchecs : {result.failed}",
        )
        self._refresh()

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importer un morceau",
            "",
            "Partitions (*.mid *.midi *.gp3 *.gp4 *.gp5);;Tous (*.*)",
        )
        if not path:
            return
        try:
            song = import_song(Path(path))
            self._repo.upsert_song(song)
            self._refresh()
            self._open_game(song)
        except Exception as exc:
            QMessageBox.warning(self, "Import impossible", str(exc))

    def _play_selected(self) -> None:
        item = self._list.currentItem()
        if item is None:
            QMessageBox.information(self, "FretFlow", "Sélectionnez un morceau ou lancez la démo.")
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        try:
            song = import_song(Path(path))
            self._open_game(song)
        except Exception as exc:
            QMessageBox.warning(self, "Impossible d'ouvrir", str(exc))

    def _play_demo(self) -> None:
        from fretflow.core.models import Measure, Note, Song, Track

        notes = [
            Note(start_seconds=i * 0.5, duration_seconds=0.4, midi_pitch=p)
            for i, p in enumerate([60, 62, 64, 65, 67, 69, 71, 72])
        ]
        song = Song(
            title="Demo C Major",
            artist="FretFlow",
            tempo_bpm=120.0,
            tracks=[Track(name="Demo", measures=[Measure(0, 0.0, 4.5, notes=notes)])],
            duration_seconds=4.5,
        )
        self._open_game(song)

    def _open_dashboard(self) -> None:
        self._dashboard = DashboardWindow()
        self._dashboard.show()

    def _open_game(self, song) -> None:
        settings = PracticeSettings(song_id=song.id, tempo_factor=1.0)
        self._game = GameWindow(song=song, settings=settings)
        self._game.show()

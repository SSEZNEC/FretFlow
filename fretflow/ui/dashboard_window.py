"""Progress dashboard window (presentation only)."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fretflow.profile.progress import ProgressService
from fretflow.ui.colors import BG, SCORE, TEXT, TEXT_DIM


class DashboardWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FretFlow — Progression")
        self.resize(700, 500)
        self.setStyleSheet(
            f"QMainWindow {{ background: {BG}; }}"
            f"QLabel {{ color: {TEXT}; }}"
            f"QTableWidget {{ background: #16213e; color: {TEXT}; gridline-color: #0f3460; }}"
            f"QHeaderView::section {{ background: #0f3460; color: {TEXT}; padding: 4px; }}"
            f"QPushButton {{ background: #e94560; color: white; padding: 8px 16px; border: none; }}"
            f"QPushButton:hover {{ background: #ff6b81; }}"
        )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("Tableau de progression")
        title.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        self._cards = QHBoxLayout()
        layout.addLayout(self._cards)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Score", "Hits", "Miss", "Precision"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table, stretch=1)

        btn_row = QHBoxLayout()
        refresh = QPushButton("Actualiser")
        refresh.clicked.connect(self.refresh)
        btn_row.addWidget(refresh)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.refresh()

    def _add_card(self, label: str, value: str) -> None:
        box = QVBoxLayout()
        v = QLabel(value)
        v.setFont(QFont("Sans", 20, QFont.Weight.Bold))
        v.setStyleSheet(f"color: {SCORE};")
        l = QLabel(label)
        l.setStyleSheet(f"color: {TEXT_DIM};")
        box.addWidget(v)
        box.addWidget(l)
        w = QWidget()
        w.setLayout(box)
        self._cards.addWidget(w)

    def refresh(self) -> None:
        while self._cards.count():
            item = self._cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        summary = ProgressService().summary(days=30)
        self._add_card("Seances", str(summary.total_sessions))
        self._add_card("Minutes", f"{summary.total_minutes:.0f}")
        self._add_card("Precision moy.", f"{summary.average_accuracy:.0%}")
        self._add_card("Meilleur score", str(summary.best_score))

        self._table.setRowCount(0)
        for s in summary.recent_sessions:
            row = self._table.rowCount()
            self._table.insertRow(row)
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(s["started_at"]))
            total = s["notes_hit"] + s["notes_missed"]
            acc = f"{s['notes_hit'] / total:.0%}" if total else "—"
            for col, val in enumerate(
                [ts, str(s["score"]), str(s["notes_hit"]), str(s["notes_missed"]), acc]
            ):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, col, item)

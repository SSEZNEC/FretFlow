"""Teacher Panel — live coaching comments (Zone 3)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from fretflow.coach.teacher_tips import TeacherTip, TipKind


_KIND_PREFIX = {
    TipKind.PREPARE: "→",
    TipKind.TECHNIQUE: "✦",
    TipKind.ENCOURAGE: "✔",
    TipKind.ANTICIPATE: "…",
    TipKind.CORRECT: "≈",
    TipKind.INFO: "•",
}


class TeacherPanel(QWidget):
    """Scrolling teacher comments — encouraging, never harsh."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Professeur")
        title.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #eaeaea;")
        layout.addWidget(title)

        self._live = QLabel("En attente de la lecture…")
        self._live.setWordWrap(True)
        self._live.setStyleSheet("color: #2ecc71; font-size: 13px; padding: 6px;")
        self._live.setMinimumHeight(48)
        layout.addWidget(self._live)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            "QTextEdit { background: #16213e; color: #ccc; border: 1px solid #0f3460; "
            "font-size: 12px; }"
        )
        layout.addWidget(self._log, stretch=1)

        self.setStyleSheet("background: #1a1a2e;")

    def show_tips(self, tips: list[TeacherTip]) -> None:
        if not tips:
            return
        primary = tips[0]
        prefix = _KIND_PREFIX.get(primary.kind, "•")
        self._live.setText(f"{prefix}  {primary.message}")
        for tip in tips:
            p = _KIND_PREFIX.get(tip.kind, "•")
            self._log.append(f"{p} {tip.message}")

    def show_message(self, message: str) -> None:
        self._live.setText(message)
        self._log.append(message)

    def show_dialogue(self, lines: list[str]) -> None:
        self._log.append("—— Fin de séance ——")
        for line in lines:
            self._log.append(line)
            self._live.setText(line)

    def clear(self) -> None:
        self._live.setText("En attente de la lecture…")
        self._log.clear()

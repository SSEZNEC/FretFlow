"""Compact chord diagram widget (vertical fretboard snippet)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from fretflow.practice.fretboard import FretPosition

_BG = QColor("#16213e")
_LINE = QColor("#aaa")
_DOT = QColor("#2ecc71")
_TEXT = QColor("#eee")


class ChordDiagramWidget(QWidget):
    """Shows a small 5-fret chord diagram with finger numbers."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = ""
        self._positions: list[FretPosition] = []
        self.setMinimumSize(90, 120)
        self.setMaximumWidth(120)

    def set_chord(self, name: str, positions: list[FretPosition]) -> None:
        self._name = name
        self._positions = list(positions)
        self.update()

    def clear(self) -> None:
        self._name = ""
        self._positions = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), _BG)

        painter.setPen(_TEXT)
        painter.setFont(QFont("Sans", 10, QFont.Weight.Bold))
        painter.drawText(8, 16, self._name or "—")

        if not self._positions:
            return

        frets_used = [p.fret for p in self._positions if p.fret > 0]
        base = min(frets_used) if frets_used else 1
        base = max(1, base)

        ml, mt = 18, 28
        cell_w, cell_h = 12, 14
        strings, frets = 6, 5

        # Grid
        painter.setPen(QPen(_LINE, 1))
        for s in range(strings):
            x = ml + s * cell_w
            painter.drawLine(x, mt, x, mt + frets * cell_h)
        for f in range(frets + 1):
            y = mt + f * cell_h
            painter.drawLine(ml, y, ml + (strings - 1) * cell_w, y)

        # Base fret label
        if base > 1:
            painter.setPen(_TEXT)
            painter.setFont(QFont("Sans", 8))
            painter.drawText(2, mt + cell_h, str(base))

        # Dots
        for pos in self._positions:
            if not (1 <= pos.string <= 6):
                continue
            # string 1 (high E) on the right of diagram convention for chords
            sx = ml + (6 - pos.string) * cell_w
            if pos.fret == 0:
                painter.setPen(QPen(_DOT, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(sx, mt - 8), 5, 5)
            else:
                fy = pos.fret - base + 1
                if not (1 <= fy <= frets):
                    continue
                cy = mt + (fy - 0.5) * cell_h
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(_DOT)
                painter.drawEllipse(QPointF(sx, cy), 6, 6)
                if pos.finger and pos.finger > 0:
                    painter.setPen(QColor("#111"))
                    painter.setFont(QFont("Sans", 7, QFont.Weight.Bold))
                    painter.drawText(int(sx - 3), int(cy + 3), str(pos.finger))

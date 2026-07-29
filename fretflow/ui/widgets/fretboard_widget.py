"""FretboardWidget — permanent guitar neck display synchronised with the song."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from fretflow.practice.fretboard import FretMarker, FretPosition

# Colours per marker role
_MARKER_COLORS = {
    FretMarker.CURRENT: QColor("#2ecc71"),   # green — play now
    FretMarker.NEXT: QColor("#3498db"),      # blue — upcoming
    FretMarker.HELD: QColor("#f39c12"),      # orange — held / chord
    FretMarker.ERROR: QColor("#e74c3c"),     # red — mistake
    FretMarker.PREVIEW: QColor("#9b59b6"),   # purple
}

_BG = QColor("#1a1a2e")
_FRET_LINE = QColor("#4a4a6a")
_STRING_LINE = QColor("#c0c0d0")
_MARKER_DOT = QColor("#3a3a5c")
_TEXT = QColor("#eaeaea")
_NUT = QColor("#e8d5a3")

# Inlay frets (standard)
_INLAYS = {3, 5, 7, 9, 12, 15, 17, 19, 21, 24}


class FretboardWidget(QWidget):
    """Draws a 6-string / 24-fret guitar neck with live positions."""

    def __init__(self, parent: QWidget | None = None, frets: int = 15) -> None:
        super().__init__(parent)
        self._frets = frets
        self._positions: list[FretPosition] = []
        self._chord_name: str | None = None
        self._info_line: str = ""
        self.setMinimumHeight(160)
        self.setMinimumWidth(400)

    def set_positions(
        self,
        positions: list[FretPosition],
        chord_name: str | None = None,
        info: str = "",
    ) -> None:
        self._positions = list(positions)
        self._chord_name = chord_name
        self._info_line = info
        self.update()

    def clear(self) -> None:
        self._positions = []
        self._chord_name = None
        self._info_line = ""
        self.update()

    # ------------------------------------------------------------------ paint

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), _BG)

        margin_left = 36
        margin_right = 12
        margin_top = 28
        margin_bottom = 20
        w = self.width() - margin_left - margin_right
        h = self.height() - margin_top - margin_bottom

        n_frets = self._frets
        n_strings = 6
        fret_w = w / n_frets
        string_h = h / (n_strings - 1) if n_strings > 1 else h

        def string_y(string: int) -> float:
            # string 1 (high E) at top
            return margin_top + (string - 1) * string_h

        def fret_x(fret: int) -> float:
            # fret 0 = nut, fret 1 = first fret line, etc.
            return margin_left + fret * fret_w

        # Inlay markers
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_MARKER_DOT)
        for fret in _INLAYS:
            if fret > n_frets:
                continue
            cx = fret_x(fret) - fret_w / 2
            if fret == 12 or fret == 24:
                for sy in (string_y(2), string_y(5)):
                    painter.drawEllipse(QPointF(cx, sy), 4, 4)
            else:
                painter.drawEllipse(QPointF(cx, string_y(3.5)), 4, 4)

        # Nut
        painter.setPen(QPen(_NUT, 4))
        painter.drawLine(
            QPointF(fret_x(0), margin_top - 4),
            QPointF(fret_x(0), margin_top + h + 4),
        )

        # Fret lines
        painter.setPen(QPen(_FRET_LINE, 1))
        for f in range(1, n_frets + 1):
            x = fret_x(f)
            painter.drawLine(QPointF(x, margin_top), QPointF(x, margin_top + h))

        # Strings
        for s in range(1, n_strings + 1):
            thickness = 1.0 + (s - 1) * 0.35
            painter.setPen(QPen(_STRING_LINE, thickness))
            y = string_y(s)
            painter.drawLine(QPointF(margin_left, y), QPointF(margin_left + w, y))

        # Fret numbers
        painter.setPen(_TEXT)
        font = QFont("Sans", 8)
        painter.setFont(font)
        for f in range(1, n_frets + 1):
            if f in _INLAYS or f == 1:
                painter.drawText(
                    int(fret_x(f) - fret_w / 2 - 6),
                    int(margin_top + h + 16),
                    str(f),
                )

        # Positions
        for pos in self._positions:
            if pos.fret > n_frets:
                continue
            color = _MARKER_COLORS.get(pos.marker, _MARKER_COLORS[FretMarker.CURRENT])
            if pos.fret == 0:
                # Open string: circle left of nut
                cx = margin_left - 14
            else:
                cx = fret_x(pos.fret) - fret_w / 2
            cy = string_y(pos.string)
            radius = 10 if pos.marker is FretMarker.CURRENT else 8
            painter.setPen(QPen(color.darker(120), 2))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

            # Finger number
            if pos.finger and pos.finger > 0:
                painter.setPen(QColor("#111"))
                painter.setFont(QFont("Sans", 8, QFont.Weight.Bold))
                painter.drawText(
                    int(cx - 4), int(cy + 4), str(pos.finger)
                )

        # Chord name / info
        painter.setPen(_TEXT)
        painter.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        header = self._chord_name or ""
        if self._info_line:
            header = f"{header}  {self._info_line}".strip()
        if header:
            painter.drawText(margin_left, 18, header)

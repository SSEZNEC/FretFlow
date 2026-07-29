"""Note highway widget — pure presentation of timeline + playhead."""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from fretflow.core.models import Note
from fretflow.ui.colors import (
    BG,
    GRID,
    HIT_LINE,
    JUDGMENT_COLORS,
    LANE,
    NOTE_COLORS,
    TEXT,
)


@dataclass(slots=True)
class VisibleNote:
    note: Note
    hit: bool = False
    judgment_name: str | None = None


class HighwayWidget(QWidget):
    """Vertical-scrolling highway. Time flows toward the hit line at the bottom.

    The widget does **not** own the game clock; the parent pushes
    ``song_time`` via ``set_song_time``.
    """

    key_pressed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(480, 360)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._notes: list[VisibleNote] = []
        self._song_time: float = 0.0
        self._look_ahead: float = 3.0  # seconds of future visible
        self._look_behind: float = 0.4
        self._last_judgment: str | None = None
        self._judgment_ttl: int = 0
        self._score: int = 0
        self._combo: int = 0
        self._accuracy_text: str = "—"

        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(50)
        self._flash_timer.timeout.connect(self._decay_judgment)
        # Started only when a judgment is shown

    def set_notes(self, notes: list[Note]) -> None:
        self._notes = [VisibleNote(note=n) for n in notes]
        self._starts = [n.start_seconds for n in notes]
        self.update()

    def set_song_time(self, t: float) -> None:
        self._song_time = t
        self.update()

    def mark_hit(self, midi_pitch: int, expected_seconds: float, judgment_name: str) -> None:
        for vn in self._notes:
            if (
                not vn.hit
                and vn.note.midi_pitch == midi_pitch
                and abs(vn.note.start_seconds - expected_seconds) < 0.02
            ):
                vn.hit = True
                vn.judgment_name = judgment_name
                break
        self._last_judgment = judgment_name
        self._judgment_ttl = 20
        if not self._flash_timer.isActive():
            self._flash_timer.start()
        self.update()

    def set_hud(self, score: int, combo: int, accuracy_text: str) -> None:
        self._score = score
        self._combo = combo
        self._accuracy_text = accuracy_text
        self.update()

    def _decay_judgment(self) -> None:
        if self._judgment_ttl > 0:
            self._judgment_ttl -= 1
            if self._judgment_ttl == 0:
                self._last_judgment = None
                self._flash_timer.stop()
            self.update()


    def keyPressEvent(self, event) -> None:  # noqa: N802
        text = event.text()
        if text:
            self.key_pressed.emit(text)
        super().keyPressEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        painter.fillRect(0, 0, w, h, QColor(BG))

        # Lanes (6 guitar strings visual guide)
        lane_w = w / 6
        for i in range(7):
            x = int(i * lane_w)
            painter.setPen(QPen(QColor(LANE), 1))
            painter.drawLine(x, 0, x, h)

        # Hit line near bottom
        hit_y = int(h * 0.85)
        painter.setPen(QPen(QColor(HIT_LINE), 3))
        painter.drawLine(0, hit_y, w, hit_y)

        # Beat grid
        painter.setPen(QPen(QColor(GRID), 1))
        t0 = self._song_time - self._look_behind
        t1 = self._song_time + self._look_ahead
        beat = 0.5  # visual grid every 0.5s
        t = int(t0 / beat) * beat
        while t < t1:
            y = self._time_to_y(t, hit_y, h)
            if 0 <= y <= h:
                painter.drawLine(0, y, w, y)
            t += beat

        # Notes — only the visible time window (bisect)
        starts = getattr(self, "_starts", None)
        if starts is None:
            starts = [vn.note.start_seconds for vn in self._notes]
            self._starts = starts
        lo = bisect.bisect_left(starts, t0)
        hi = bisect.bisect_right(starts, t1)
        for vn in self._notes[lo:hi]:
            n = vn.note
            y = self._time_to_y(n.start_seconds, hit_y, h)
            # Map pitch to lane (mod 6 for visual spread)
            lane = (n.midi_pitch % 12) % 6
            cx = int((lane + 0.5) * lane_w)
            color = QColor(NOTE_COLORS[n.midi_pitch % 12])
            if vn.hit:
                color.setAlpha(80)
            radius = 14
            # Long note body
            if n.duration_seconds > 0.15:
                y_end = self._time_to_y(n.start_seconds + n.duration_seconds, hit_y, h)
                painter.setPen(QPen(color, 6))
                painter.drawLine(cx, y, cx, y_end)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - radius, y - radius, radius * 2, radius * 2)

        # HUD
        painter.setPen(QColor(TEXT))
        font = QFont("Sans", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(12, 28, f"Score  {self._score}")
        painter.drawText(12, 52, f"Combo  {self._combo}")
        painter.drawText(12, 76, f"Préc.  {self._accuracy_text}")

        if self._last_judgment and self._judgment_ttl > 0:
            jc = QColor(JUDGMENT_COLORS.get(self._last_judgment, TEXT))
            painter.setPen(jc)
            big = QFont("Sans", 28, QFont.Weight.Bold)
            painter.setFont(big)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._last_judgment)

        painter.end()

    def _time_to_y(self, song_t: float, hit_y: int, h: int) -> int:
        """Map song time to y pixel. Future notes are above the hit line."""
        dt = song_t - self._song_time
        # dt=0 → hit_y; dt=+look_ahead → top
        span = self._look_ahead + self._look_behind
        frac = (self._look_ahead - dt) / span if span else 0.5
        return int(frac * hit_y)

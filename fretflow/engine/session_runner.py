"""Run a practice session: match played notes against the timeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fretflow.core.config import JudgmentWindows
from fretflow.core.models import Note, PerformanceReport, Session, Song, Track
from fretflow.engine.clock import GameClock
from fretflow.engine.events import HitEvent, MissEvent, PlayedNoteEvent
from fretflow.engine.judgment import Judgment, judge_note
from fretflow.engine.score import next_combo, points_for
from fretflow.practice.loop import LoopRegion
from fretflow.practice.settings import PracticeSettings

logger = logging.getLogger("fretflow.engine.session_runner")


@dataclass(slots=True)
class _PendingNote:
    note: Note
    index: int


@dataclass(slots=True)
class SessionRunner:
    """Stateful runner that judges input against expected notes."""

    song: Song
    settings: PracticeSettings
    windows: JudgmentWindows = field(default_factory=JudgmentWindows)
    session_id: UUID = field(default_factory=uuid4)

    clock: GameClock = field(init=False)
    loop: LoopRegion | None = field(init=False, default=None)
    _notes: list[Note] = field(init=False, default_factory=list)
    _next_index: int = field(init=False, default=0)
    _combo: int = field(init=False, default=0)
    _max_combo: int = field(init=False, default=0)
    _score: int = field(init=False, default=0)
    _hits: int = field(init=False, default=0)
    _misses: int = field(init=False, default=0)
    _offsets_ms: list[float] = field(init=False, default_factory=list)
    _hit_events: list[HitEvent] = field(init=False, default_factory=list)
    _miss_events: list[MissEvent] = field(init=False, default_factory=list)
    _started_at: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        track = self._select_track()
        start = self.settings.section_start_seconds or 0.0
        end = self.settings.section_end_seconds
        notes = [
            n
            for n in track.notes
            if n.start_seconds >= start and (end is None or n.start_seconds < end)
        ]
        notes.sort(key=lambda n: (n.start_seconds, n.midi_pitch))
        self._notes = notes

        duration = end if end is not None else self.song.duration_seconds
        if notes and (end is None):
            duration = max(duration, max(n.start_seconds + n.duration_seconds for n in notes))

        self.clock = GameClock(
            duration_seconds=duration or self.song.duration_seconds,
            tempo_factor=self.settings.tempo_factor,
            song_time=start,
        )

        if self.settings.loop_enabled and end is not None:
            self.loop = LoopRegion(start_seconds=start, end_seconds=end, enabled=True)

        import time as _time

        self._started_at = _time.time()

    def _select_track(self) -> Track:
        tracks = self.song.tracks
        if not tracks:
            raise ValueError("Song has no tracks")
        idx = self.settings.track_index
        if idx < 0 or idx >= len(tracks):
            raise ValueError(f"track_index {idx} out of range (0..{len(tracks) - 1})")
        return tracks[idx]

    def start(self) -> None:
        self.clock.start()

    def pause(self) -> None:
        self.clock.pause()

    def resume(self) -> None:
        self.clock.resume()

    def seek(self, song_seconds: float) -> None:
        self.clock.seek(song_seconds)
        # Rewind pending note cursor
        self._next_index = 0
        while (
            self._next_index < len(self._notes)
            and self._notes[self._next_index].start_seconds < song_seconds - 0.5
        ):
            self._next_index += 1

    def tick(self) -> list[MissEvent]:
        """Advance logic: auto-miss notes that passed the good window.

        Call this periodically (e.g. every frame or from the CLI loop).
        """
        now = self.clock.current_time()
        misses: list[MissEvent] = []

        # Loop wrap
        if self.loop and self.loop.should_wrap(now):
            self.clock.seek(self.loop.wrap_target())
            self._next_index = 0
            while (
                self._next_index < len(self._notes)
                and self._notes[self._next_index].start_seconds < self.loop.start_seconds
            ):
                self._next_index += 1
            return misses

        good_s = self.windows.good_ms / 1000.0
        while self._next_index < len(self._notes):
            note = self._notes[self._next_index]
            if note.start_seconds + good_s < now:
                # Missed
                self._combo = 0
                self._misses += 1
                event = MissEvent(
                    expected_seconds=note.start_seconds,
                    midi_pitch=note.midi_pitch,
                    combo=self._combo,
                )
                self._miss_events.append(event)
                misses.append(event)
                self._next_index += 1
            else:
                break
        return misses

    def handle_played_note(self, event: PlayedNoteEvent) -> HitEvent | None:
        """Match a played note to the nearest pending expected note of same pitch."""
        self.tick()  # clear overdue misses first

        best_idx: int | None = None
        best_abs_offset = float("inf")
        good_s = self.windows.good_ms / 1000.0

        for i in range(self._next_index, len(self._notes)):
            note = self._notes[i]
            if note.start_seconds - event.time_seconds > good_s:
                break  # too far in the future
            if note.midi_pitch != event.midi_pitch:
                continue
            offset = abs(event.time_seconds - note.start_seconds)
            if offset < best_abs_offset:
                best_abs_offset = offset
                best_idx = i

        if best_idx is None:
            return None

        note = self._notes[best_idx]
        result = judge_note(note.start_seconds, event.time_seconds, self.windows)
        if result.judgment is Judgment.MISS:
            return None

        # Consume this note and any skipped ones before it as misses
        for j in range(self._next_index, best_idx):
            skipped = self._notes[j]
            self._misses += 1
            self._combo = 0
            self._miss_events.append(
                MissEvent(
                    expected_seconds=skipped.start_seconds,
                    midi_pitch=skipped.midi_pitch,
                    combo=0,
                )
            )
        self._next_index = best_idx + 1

        self._combo = next_combo(self._combo, result.judgment)
        self._max_combo = max(self._max_combo, self._combo)
        pts = points_for(result.judgment, self._combo)
        self._score += pts
        self._hits += 1
        self._offsets_ms.append(result.offset_ms)

        hit = HitEvent(
            expected_seconds=note.start_seconds,
            played_seconds=event.time_seconds,
            midi_pitch=note.midi_pitch,
            judgment=result.judgment,
            offset_ms=result.offset_ms,
            combo=self._combo,
            score=self._score,
        )
        self._hit_events.append(hit)
        return hit

    def build_session(self) -> Session:
        import time as _time

        duration = _time.time() - self._started_at
        return Session(
            id=self.session_id,
            song_id=self.song.id,
            started_at=self._started_at,
            duration_seconds=duration,
            notes_hit=self._hits,
            notes_missed=self._misses,
            notes_expected=len(self._notes),
            score=self._score,
            max_combo=self._max_combo,
            tempo_factor=self.settings.tempo_factor,
            section_start_seconds=self.settings.section_start_seconds,
            section_end_seconds=self.settings.section_end_seconds,
        )

    def build_report(self) -> PerformanceReport:
        avg_offset = (
            sum(self._offsets_ms) / len(self._offsets_ms) if self._offsets_ms else 0.0
        )
        accuracy = (
            self._hits / (self._hits + self._misses)
            if (self._hits + self._misses) > 0
            else 0.0
        )
        recommendations: list[str] = []
        if accuracy < 0.7:
            recommendations.append(
                "Précision faible : ralentissez le tempo (ex. 70 %) et travaillez en boucle."
            )
        if self._offsets_ms and avg_offset > 20:
            recommendations.append(
                "Vous jouez en retard en moyenne — anticipez légèrement les notes."
            )
        elif self._offsets_ms and avg_offset < -20:
            recommendations.append(
                "Vous jouez en avance en moyenne — attendez un peu plus le temps fort."
            )
        if not recommendations:
            recommendations.append("Bonne séance — essayez d'augmenter légèrement le tempo.")

        return PerformanceReport(
            session_id=self.session_id,
            accuracy=accuracy,
            average_offset_ms=avg_offset,
            recommendations=recommendations,
            notes_expected=len(self._notes),
            notes_hit=self._hits,
            notes_missed=self._misses,
            max_combo=self._max_combo,
            score=self._score,
        )

    @property
    def expected_count(self) -> int:
        return len(self._notes)

    @property
    def progress(self) -> float:
        if not self._notes:
            return 1.0
        return min(1.0, self._next_index / len(self._notes))

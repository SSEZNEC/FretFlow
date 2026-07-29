"""Real-time teacher tips — short, encouraging, never judgmental."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from fretflow.core.models import Note, Technique
from fretflow.practice.fretboard import FretPosition


class TipKind(Enum):
    PREPARE = auto()
    TECHNIQUE = auto()
    ENCOURAGE = auto()
    ANTICIPATE = auto()
    CORRECT = auto()
    INFO = auto()


@dataclass(slots=True, frozen=True)
class TeacherTip:
    kind: TipKind
    message: str
    priority: int = 0  # higher = more urgent


@dataclass(slots=True)
class TeacherTipEngine:
    """Generates contextual tips from playhead state (pure, no UI)."""

    _last_messages: list[str] = field(default_factory=list, init=False, repr=False)

    def tips_at(
        self,
        time_seconds: float,
        notes: list[Note],
        positions: list[FretPosition],
        *,
        last_hit: bool | None = None,
        last_offset_ms: float | None = None,
        combo: int = 0,
        lookahead: float = 1.2,
    ) -> list[TeacherTip]:
        tips: list[TeacherTip] = []

        # Upcoming techniques
        for note in notes:
            delta = note.start_seconds - time_seconds
            if 0.15 < delta <= lookahead:
                if note.technique is Technique.BEND:
                    tips.append(TeacherTip(TipKind.TECHNIQUE, "Prépare le bend — vise la justesse.", 3))
                elif note.technique is Technique.SLIDE:
                    tips.append(TeacherTip(TipKind.TECHNIQUE, "Attention au slide qui arrive.", 3))
                elif note.technique is Technique.HAMMER_ON:
                    tips.append(TeacherTip(TipKind.TECHNIQUE, "Hammer-on en approche — doigt ferme.", 2))
                elif note.technique is Technique.PULL_OFF:
                    tips.append(TeacherTip(TipKind.TECHNIQUE, "Pull-off à venir — relâche proprement.", 2))
                elif note.technique is Technique.PALM_MUTE:
                    tips.append(TeacherTip(TipKind.TECHNIQUE, "Palm mute — main droite près du chevalet.", 2))

        # Barre / position jumps
        current = [p for p in positions if p.marker.name == "CURRENT"]
        upcoming = [p for p in positions if p.marker.name == "NEXT"]
        if len(current) >= 4:
            frets = {p.fret for p in current if p.fret and p.fret > 0}
            if len(frets) == 1:
                tips.append(TeacherTip(TipKind.PREPARE, "Prépare ton barré — pression uniforme.", 4))
        if current and upcoming:
            cf = current[0].fret
            nf = upcoming[0].fret
            if cf is not None and nf is not None and abs(nf - cf) >= 4:
                tips.append(
                    TeacherTip(
                        TipKind.ANTICIPATE,
                        f"Grand déplacement : case {cf} → {nf}. Anticipe le glissement.",
                        3,
                    )
                )

        # Encouragement from recent performance
        if last_hit is True and last_offset_ms is not None:
            if abs(last_offset_ms) <= 20:
                tips.append(TeacherTip(TipKind.ENCOURAGE, "Excellent timing.", 1))
            elif last_offset_ms > 30:
                tips.append(TeacherTip(TipKind.CORRECT, "Un peu en retard — anticipe l'attaque.", 2))
            elif last_offset_ms < -30:
                tips.append(TeacherTip(TipKind.CORRECT, "Un peu en avance — pose-toi sur le temps.", 2))
        if combo >= 5 and combo % 5 == 0:
            tips.append(TeacherTip(TipKind.ENCOURAGE, f"Belle série : {combo} notes d'affilée.", 1))

        # Deduplicate by message, keep highest priority
        tips.sort(key=lambda t: t.priority, reverse=True)
        seen: set[str] = set()
        unique: list[TeacherTip] = []
        for tip in tips:
            if tip.message not in seen:
                seen.add(tip.message)
                unique.append(tip)
        return unique[:3]

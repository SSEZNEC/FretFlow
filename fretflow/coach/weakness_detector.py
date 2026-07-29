"""Detect pedagogical weaknesses from a SessionReport (pure functions)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from fretflow.coach.skills import SkillId
from fretflow.practice.session_report import SectionStats, SessionReport


class WeaknessKind(Enum):
    LOW_ACCURACY = auto()
    SYSTEMATIC_LATE = auto()
    SYSTEMATIC_EARLY = auto()
    HARD_SECTION = auto()
    UNSTABLE_TEMPO = auto()
    TECHNIQUE_GAP = auto()


@dataclass(slots=True, frozen=True)
class Weakness:
    """An explainable finding tied to observable data."""

    kind: WeaknessKind
    skill_id: SkillId
    severity: float  # 0..1
    message: str
    section: SectionStats | None = None
    evidence: str = ""


def detect_weaknesses(
    report: SessionReport,
    *,
    late_threshold_ms: float = 25.0,
    early_threshold_ms: float = -25.0,
    hard_accuracy: float = 0.75,
) -> list[Weakness]:
    """Analyse a session report and return ranked weaknesses. Pure."""
    findings: list[Weakness] = []

    if report.notes_expected == 0:
        return findings

    if report.accuracy < 0.7:
        severity = 1.0 - report.accuracy
        findings.append(
            Weakness(
                kind=WeaknessKind.LOW_ACCURACY,
                skill_id=SkillId.PITCH_ACCURACY,
                severity=min(1.0, severity),
                message=(
                    f"Precision globale de {report.accuracy:.0%} "
                    f"({report.notes_hit}/{report.notes_expected})."
                ),
                evidence=f"accuracy={report.accuracy:.3f}",
            )
        )

    bias = report.late_bias_ms()
    if bias >= late_threshold_ms:
        findings.append(
            Weakness(
                kind=WeaknessKind.SYSTEMATIC_LATE,
                skill_id=SkillId.RHYTHM_TIMING,
                severity=min(1.0, abs(bias) / 80.0),
                message=f"Jeu systematiquement en retard ({bias:+.0f} ms en moyenne).",
                evidence=f"avg_offset_ms={bias:.1f}",
            )
        )
    elif bias <= early_threshold_ms:
        findings.append(
            Weakness(
                kind=WeaknessKind.SYSTEMATIC_EARLY,
                skill_id=SkillId.RHYTHM_TIMING,
                severity=min(1.0, abs(bias) / 80.0),
                message=f"Jeu systematiquement en avance ({bias:+.0f} ms en moyenne).",
                evidence=f"avg_offset_ms={bias:.1f}",
            )
        )

    for section in report.hard_sections(max_accuracy=hard_accuracy):
        severity = 1.0 - section.accuracy
        findings.append(
            Weakness(
                kind=WeaknessKind.HARD_SECTION,
                skill_id=SkillId.SECTION_ENDURANCE,
                severity=min(1.0, severity),
                message=(
                    f"Passage difficile {section.start_seconds:.1f}s-"
                    f"{section.end_seconds:.1f}s ({section.accuracy:.0%} de reussite)."
                ),
                section=section,
                evidence=(
                    f"section={section.start_seconds:.1f}-{section.end_seconds:.1f} "
                    f"acc={section.accuracy:.3f}"
                ),
            )
        )

    findings.sort(key=lambda w: w.severity, reverse=True)
    return findings

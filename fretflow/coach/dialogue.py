"""Post-session dialogue — human, encouraging coach voice."""

from __future__ import annotations

from fretflow.coach.skills import SkillId, SkillProfile
from fretflow.coach.weakness_detector import Weakness, WeaknessKind
from fretflow.practice.session_report import SessionReport


def build_dialogue(
    report: SessionReport,
    weaknesses: list[Weakness],
    profile: SkillProfile | None = None,
) -> list[str]:
    """Return short spoken-style lines for the teacher panel / report."""
    lines: list[str] = []

    if report.notes_expected == 0:
        return ["Pas assez de données pour un conseil utile. Rejouez quelques mesures."]

    acc = report.accuracy
    if acc >= 0.9:
        lines.append("Tu progresses clairement — la précision est solide.")
    elif acc >= 0.75:
        lines.append("Bonne séance. La base est là, on peut viser encore plus de régularité.")
    elif acc >= 0.5:
        lines.append("Tu construis quelque chose. Ralentis un peu : la qualité viendra avant la vitesse.")
    else:
        lines.append(
            "Ce passage demande du temps. Ce n'est pas un échec — c'est exactement "
            "le genre de défi qui fait progresser."
        )

    if abs(report.average_offset_ms) <= 15 and report.notes_hit > 0:
        lines.append("Le tempo est stable. Excellent point.")
    elif report.average_offset_ms > 25:
        lines.append("Tu arrives souvent un peu après le temps. Anticipe l'attaque.")
    elif report.average_offset_ms < -25:
        lines.append("Tu devances parfois le temps. Pose-toi sur chaque pulse.")

    for w in weaknesses[:2]:
        if w.kind is WeaknessKind.HARD_SECTION and w.section is not None:
            s = w.section
            lines.append(
                f"Le passage {s.start_seconds:.0f}s–{s.end_seconds:.0f}s te résiste. "
                "On le bouclera au ralenti."
            )
        elif w.kind is WeaknessKind.SYSTEMATIC_LATE:
            lines.append("Le retard est systématique — un exercice de métronome t'aidera.")

    if profile is not None:
        strong = profile.strongest(1)
        weak = profile.weakest(1)
        if strong:
            lines.append(f"Point fort du moment : {strong[0].label_fr}.")
        if weak and weak[0].level < 0.5:
            lines.append(f"À travailler en douceur : {weak[0].label_fr}.")

    lines.append(
        f"Temps utile : {report.duration_seconds / 60:.1f} min. "
        "Reviens demain, même 10 minutes comptent."
    )
    return lines

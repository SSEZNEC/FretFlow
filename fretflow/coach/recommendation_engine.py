"""Turn weaknesses + skill profile into concrete Exercise recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from fretflow.coach.skills import SkillId, SkillProfile
from fretflow.coach.weakness_detector import Weakness, WeaknessKind, detect_weaknesses
from fretflow.practice.exercise import Exercise, ExerciseKind
from fretflow.practice.exercise_plan import ExercisePlan
from fretflow.practice.session_report import SessionReport


@dataclass(slots=True, frozen=True)
class Recommendation:
    """An explainable recommendation with a ready-to-run exercise."""

    summary: str
    rationale: str
    exercise: Exercise
    related_skill: SkillId
    priority: float  # 0..1


@dataclass(slots=True)
class RecommendationEngine:
    """Stateless coach core: report in, recommendations out."""

    default_tempo_factor: float = 0.7
    max_recommendations: int = 3

    def recommend(
        self,
        report: SessionReport,
        skill_profile: SkillProfile | None = None,
    ) -> list[Recommendation]:
        weaknesses = detect_weaknesses(report)
        profile = skill_profile or SkillProfile()
        self._update_skills(profile, report, weaknesses)

        recs: list[Recommendation] = []
        seen_kinds: set[WeaknessKind] = set()

        for w in weaknesses:
            if w.kind in seen_kinds:
                continue
            seen_kinds.add(w.kind)
            rec = self._from_weakness(w, report)
            if rec is not None:
                recs.append(rec)
            if len(recs) >= self.max_recommendations:
                break

        if not recs and report.notes_expected > 0:
            recs.append(
                Recommendation(
                    summary="Bonne base — montez legerement le tempo.",
                    rationale=(
                        f"Precision {report.accuracy:.0%} a tempo x{report.tempo_factor:.2f}. "
                        "Augmenter de 5-10 % pour progresser."
                    ),
                    exercise=Exercise(
                        title="Passe complete un peu plus rapide",
                        kind=ExerciseKind.SIGHT_READING,
                        song_id=report.song_id,
                        tempo_factor=min(1.0, report.tempo_factor + 0.1),
                        instructions="Rejouez en visant la meme precision.",
                    ),
                    related_skill=SkillId.TEMPO_STABILITY,
                    priority=0.3,
                )
            )

        recs.sort(key=lambda r: r.priority, reverse=True)
        return recs[: self.max_recommendations]

    def build_plan(
        self,
        report: SessionReport,
        skill_profile: SkillProfile | None = None,
        title: str = "Plan post-session",
    ) -> ExercisePlan:
        recs = self.recommend(report, skill_profile)
        plan = ExercisePlan(
            title=title,
            goal_summary="Consolider les points faibles de la derniere seance.",
        )
        for rec in recs:
            plan.add(rec.exercise)
        if plan.exercises:
            plan.estimated_minutes = sum(
                (ex.duration_hint_seconds or 60.0) * ex.target_repetitions / 60.0
                for ex in plan.exercises
            )
        return plan

    def _from_weakness(self, w: Weakness, report: SessionReport) -> Recommendation | None:
        song_id = report.song_id

        if w.kind is WeaknessKind.HARD_SECTION and w.section is not None:
            sec = w.section
            return Recommendation(
                summary=(
                    f"Boucler le passage {sec.start_seconds:.0f}s-"
                    f"{sec.end_seconds:.0f}s au ralenti."
                ),
                rationale=w.message,
                exercise=Exercise(
                    title=f"Boucle {sec.start_seconds:.0f}-{sec.end_seconds:.0f}s",
                    kind=ExerciseKind.SECTION_LOOP,
                    song_id=song_id,
                    section_start_seconds=sec.start_seconds,
                    section_end_seconds=sec.end_seconds,
                    tempo_factor=self.default_tempo_factor,
                    target_repetitions=5,
                    instructions=(
                        "Bouclez jusqu a 85 % de precision, "
                        "puis remontez le tempo par paliers de 5 %."
                    ),
                ),
                related_skill=w.skill_id,
                priority=w.severity,
            )

        if w.kind is WeaknessKind.SYSTEMATIC_LATE:
            return Recommendation(
                summary="Travailler l anticipation rythmique.",
                rationale=w.message,
                exercise=Exercise(
                    title="Timing — corriger le retard",
                    kind=ExerciseKind.TEMPO_RAMP,
                    song_id=song_id,
                    tempo_factor=max(0.5, report.tempo_factor - 0.15),
                    instructions="Ralentissez et comptez a voix haute.",
                    technique_tags=["rhythm"],
                ),
                related_skill=SkillId.RHYTHM_TIMING,
                priority=w.severity,
            )

        if w.kind is WeaknessKind.SYSTEMATIC_EARLY:
            return Recommendation(
                summary="Attendre le temps fort.",
                rationale=w.message,
                exercise=Exercise(
                    title="Timing — corriger l avance",
                    kind=ExerciseKind.TEMPO_RAMP,
                    song_id=song_id,
                    tempo_factor=max(0.5, report.tempo_factor - 0.1),
                    instructions="Posez-vous sur chaque temps.",
                    technique_tags=["rhythm"],
                ),
                related_skill=SkillId.RHYTHM_TIMING,
                priority=w.severity,
            )

        if w.kind is WeaknessKind.LOW_ACCURACY:
            return Recommendation(
                summary="Reduire le tempo et isoler les erreurs.",
                rationale=w.message,
                exercise=Exercise(
                    title="Precision au ralenti",
                    kind=ExerciseKind.SECTION_LOOP,
                    song_id=song_id,
                    tempo_factor=self.default_tempo_factor,
                    target_accuracy=0.9,
                    target_repetitions=4,
                    instructions="Priorite a la justesse, pas a la vitesse.",
                ),
                related_skill=SkillId.PITCH_ACCURACY,
                priority=w.severity,
            )

        return None

    def _update_skills(
        self,
        profile: SkillProfile,
        report: SessionReport,
        weaknesses: list[Weakness],
    ) -> None:
        offset_quality = max(0.0, 1.0 - abs(report.average_offset_ms) / 100.0)
        profile.get(SkillId.RHYTHM_TIMING).update(offset_quality)
        profile.get(SkillId.RHYTHM_TIMING).last_session_id = report.session_id

        profile.get(SkillId.PITCH_ACCURACY).update(report.accuracy)
        profile.get(SkillId.PITCH_ACCURACY).last_session_id = report.session_id

        if report.sections:
            hard = len(report.hard_sections())
            ratio_ok = 1.0 - (hard / len(report.sections))
            profile.get(SkillId.SECTION_ENDURANCE).update(ratio_ok)
            profile.get(SkillId.SECTION_ENDURANCE).last_session_id = report.session_id

        if report.tempo_factor >= 0.9:
            profile.get(SkillId.TEMPO_STABILITY).update(report.accuracy)
            profile.get(SkillId.TEMPO_STABILITY).last_session_id = report.session_id

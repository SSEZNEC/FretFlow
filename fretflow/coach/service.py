"""Coach application service — orchestrates report analysis and recommendations."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fretflow.coach.goals import GoalTracker
from fretflow.coach.recommendation_engine import Recommendation, RecommendationEngine
from fretflow.coach.skills import SkillProfile
from fretflow.coach.weakness_detector import Weakness, detect_weaknesses
from fretflow.engine.session_runner import SessionRunner
from fretflow.practice.exercise_plan import ExercisePlan
from fretflow.practice.report_builder import report_from_runner
from fretflow.practice.session_report import SessionReport
from fretflow.profile.skills_store import SkillStore

logger = logging.getLogger("fretflow.coach.service")


@dataclass(slots=True)
class CoachResult:
    report: SessionReport
    weaknesses: list[Weakness]
    recommendations: list[Recommendation]
    plan: ExercisePlan
    skill_profile: SkillProfile


class CoachService:
    """Post-session coaching facade."""

    def __init__(
        self,
        engine: RecommendationEngine | None = None,
        skill_store: SkillStore | None = None,
        goals: GoalTracker | None = None,
    ) -> None:
        self.engine = engine or RecommendationEngine()
        self.skill_store = skill_store or SkillStore()
        self.goals = goals or GoalTracker()

    def analyse_runner(self, runner: SessionRunner) -> CoachResult:
        report = report_from_runner(runner)
        return self.analyse_report(report)

    def analyse_report(self, report: SessionReport) -> CoachResult:
        profile = self.skill_store.load()
        weaknesses = detect_weaknesses(report)
        recommendations = self.engine.recommend(report, profile)
        plan = self.engine.build_plan(report, profile)

        self.skill_store.save(profile)
        self.goals.record_session(report.duration_seconds, report.accuracy)

        logger.info(
            "Coach: %d weaknesses, %d recommendations, accuracy=%.0f%%",
            len(weaknesses),
            len(recommendations),
            report.accuracy * 100,
        )
        return CoachResult(
            report=report,
            weaknesses=weaknesses,
            recommendations=recommendations,
            plan=plan,
            skill_profile=profile,
        )

    def format_result(self, result: CoachResult) -> str:
        lines = [
            "── Analyse coach ──",
            f"  Precision : {result.report.accuracy:.0%}",
            f"  Offset moy: {result.report.average_offset_ms:+.1f} ms",
            f"  Score     : {result.report.score}",
            "",
        ]
        if result.weaknesses:
            lines.append("Points faibles :")
            for w in result.weaknesses[:5]:
                lines.append(f"  • {w.message}")
            lines.append("")

        if result.recommendations:
            lines.append("Recommandations :")
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"  {i}. {rec.summary}")
                lines.append(f"     → {rec.exercise.title} (tempo ×{rec.exercise.tempo_factor:.2f})")
                if rec.exercise.has_section:
                    lines.append(
                        f"     Section {rec.exercise.section_start_seconds:.1f}s–"
                        f"{rec.exercise.section_end_seconds:.1f}s"
                    )
                lines.append(f"     {rec.rationale}")
            lines.append("")

        weakest = result.skill_profile.weakest(3)
        if weakest:
            lines.append("Skills (plus faibles) :")
            for s in weakest:
                lines.append(f"  • {s.label_fr}: {s.level:.0%} (n={s.sample_count})")
            lines.append("")

        lines.append("Objectifs :")
        for line in self.goals.summary_lines():
            lines.append(f"  {line}")

        return "\n".join(lines)

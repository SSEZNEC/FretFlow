"""Composition root and application entry point."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from uuid import UUID

from fretflow import __version__
from fretflow.core.config import load_config, write_default_config
from fretflow.core.logging import setup_logging
from fretflow.core.paths import config_dir, data_dir

logger = logging.getLogger("fretflow.app")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fretflow",
        description="FretFlow — coach d'apprentissage de la guitare",
    )
    parser.add_argument("--version", action="version", version=f"FretFlow {__version__}")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
    )
    parser.add_argument("--init-config", action="store_true")

    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Scan directories and import songs")
    scan_p.add_argument("paths", nargs="+", type=Path)
    scan_p.add_argument("--force", action="store_true")

    sub.add_parser("library", help="List songs in the local library")

    import_p = sub.add_parser("import", help="Import a single song file")
    import_p.add_argument("file", type=Path)

    practice_p = sub.add_parser(
        "practice",
        help="Run a practice session (keyboard simulation)",
    )
    practice_p.add_argument(
        "source",
        type=Path,
        help="Song file (.mid/.gp*) or leave for auto-demo",
        nargs="?",
        default=None,
    )
    practice_p.add_argument("--tempo", type=float, default=1.0, help="Tempo factor 0.5–1.0")
    practice_p.add_argument("--start", type=float, default=None, help="Section start (s)")
    practice_p.add_argument("--end", type=float, default=None, help="Section end (s)")
    practice_p.add_argument("--loop", action="store_true", help="Enable A/B loop")
    practice_p.add_argument(
        "--auto",
        action="store_true",
        help="Auto-play expected notes (demo / test mode)",
    )
    practice_p.add_argument(
        "--track",
        type=int,
        default=0,
        help="Track index (default 0)",
    )

    sub.add_parser("history", help="Show recent practice sessions")

    sub.add_parser("ui", help="Launch the graphical interface (PySide6)")

    sub.add_parser("coach", help="Show skills, goals and last coaching tips")
    prog = ear = sub.add_parser("ear-train", help="Ear training (single notes)")
    ear.add_argument("--count", type=int, default=5)
    ear.add_argument("--play", action="store_true", help="Play reference tones if audio available")
    ana = sub.add_parser("analyse-song", help="Pedagogical analysis of a song file")
    ana.add_argument("path", type=Path)
    sub.add_parser("progress", help="Show practice progress summary")
    prog.add_argument("--days", type=int, default=30)
    exp = sub.add_parser("export", help="Export session stats")
    exp.add_argument("path", type=Path, help="Output file (.json or .csv)")
    exp.add_argument("--days", type=int, default=365)

    sub.add_parser("devices", help="List audio input devices")
    diag = sub.add_parser("diagnose-audio", help="Run offline pitch detection on a synthetic tone")
    diag.add_argument("--freq", type=float, default=440.0, help="Test tone frequency Hz")

    return parser


def _cmd_scan(args: argparse.Namespace) -> int:
    from fretflow.library import LibraryScanner

    result = LibraryScanner().scan(args.paths, force=args.force)
    print(f"Importés : {result.imported}")
    print(f"Ignorés  : {result.skipped}")
    print(f"Échecs   : {result.failed}")
    for err in result.errors:
        print(f"  ! {err}")
    return 1 if result.failed and not result.imported else 0


def _cmd_library(_args: argparse.Namespace) -> int:
    from fretflow.library import SongRepository

    songs = SongRepository().list_songs()
    if not songs:
        print("Bibliothèque vide. Utilisez : fretflow scan <dossier>")
        return 0
    print(f"{'Titre':<40} {'Artiste':<20} {'BPM':>6} {'Durée':>8} {'Pistes':>6}")
    print("-" * 86)
    for s in songs:
        print(
            f"{s['title'][:40]:<40} {s['artist'][:20]:<20} "
            f"{s['tempo_bpm']:>6.0f} {float(s['duration_seconds']):>7.1f}s "
            f"{s['track_count']:>6}"
        )
    print(f"\n{len(songs)} morceau(x)")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    from fretflow.importers import import_song
    from fretflow.library import SongRepository

    song = import_song(args.file)
    SongRepository().upsert_song(song)
    print(f"Importé : {song.title} ({song.tempo_bpm:.0f} BPM, {song.duration_seconds:.1f}s)")
    for t in song.tracks:
        print(f"  - {t.name}: {len(t.notes)} note(s)")
    return 0


def _cmd_history(_args: argparse.Namespace) -> int:
    from fretflow.profile import SessionRepository

    rows = SessionRepository().list_recent(15)
    if not rows:
        print("Aucune session enregistrée.")
        return 0
    print(f"{'Date':<20} {'Score':>7} {'Hit':>5} {'Miss':>5} {'Préc.':>7} {'Tempo':>6}")
    print("-" * 60)
    for r in rows:
        total = r["notes_hit"] + r["notes_missed"]
        acc = (r["notes_hit"] / total * 100) if total else 0
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(r["started_at"]))
        print(
            f"{ts:<20} {r['score']:>7} {r['notes_hit']:>5} {r['notes_missed']:>5} "
            f"{acc:>6.0f}% {r['tempo_factor']:>5.0%}"
        )
    return 0


def _load_song_for_practice(source: Path | None):
    from fretflow.core.models import Measure, Note, Song, Track
    from fretflow.importers import import_song

    if source is not None:
        return import_song(source)

    # Built-in demo: C major ascending
    notes = [
        Note(start_seconds=i * 0.5, duration_seconds=0.4, midi_pitch=p)
        for i, p in enumerate([60, 62, 64, 65, 67, 69, 71, 72])
    ]
    measure = Measure(index=0, start_seconds=0.0, duration_seconds=4.5, notes=notes)
    track = Track(name="Demo", measures=[measure])
    return Song(
        title="Demo C Major",
        artist="FretFlow",
        tempo_bpm=120.0,
        tracks=[track],
        duration_seconds=4.5,
    )


def _cmd_practice(args: argparse.Namespace) -> int:
    from fretflow.core.config import load_config
    from fretflow.engine import PlayedNoteEvent, SessionRunner
    from fretflow.practice import PracticeSettings
    from fretflow.profile import ProfileRepository, SessionRepository

    ProfileRepository().ensure_default()
    song = _load_song_for_practice(args.source)
    config = load_config()

    settings = PracticeSettings(
        song_id=song.id,
        track_index=args.track,
        tempo_factor=args.tempo,
        section_start_seconds=args.start,
        section_end_seconds=args.end,
        loop_enabled=args.loop,
    )
    runner = SessionRunner(song=song, settings=settings, windows=config.judgment)
    track = song.tracks[args.track] if song.tracks else None
    n_notes = runner.expected_count

    print(f"═══ Pratique : {song.title} ═══")
    print(f"  Tempo ×{args.tempo:.2f}  |  Notes attendues : {n_notes}")
    if args.start is not None or args.end is not None:
        print(f"  Section : {args.start or 0:.1f}s → {args.end or 'fin'}")
    if args.loop:
        print("  Boucle A/B : activée")
    print()

    if args.auto or args.source is None:
        # Deterministic auto-play for demo / CI
        print("Mode auto-play (notes jouées à l'heure exacte)…")
        runner.start()
        notes = sorted(
            (track.notes if track else []),
            key=lambda n: n.start_seconds,
        )
        if args.start is not None:
            notes = [n for n in notes if n.start_seconds >= args.start]
        if args.end is not None:
            notes = [n for n in notes if n.start_seconds < args.end]

        for note in notes:
            # Simulate perfect timing
            runner.clock.seek(note.start_seconds)
            hit = runner.handle_played_note(
                PlayedNoteEvent(
                    midi_pitch=note.midi_pitch,
                    time_seconds=note.start_seconds,
                    velocity=note.velocity,
                )
            )
            if hit:
                print(
                    f"  [{hit.judgment.name:7}] pitch={hit.midi_pitch:3}  "
                    f"offset={hit.offset_ms:+.0f}ms  combo={hit.combo}  score={hit.score}"
                )
            time.sleep(0.01)  # tiny pause for readability
        runner.tick()
    else:
        print("Mode manuel non interactif en CLI pure.")
        print("Utilisez --auto pour une démonstration, ou l'UI (Milestone 3).")
        print("Simulation auto des notes du fichier…")
        args.auto = True
        return _cmd_practice(args)

    session = runner.build_session()
    SessionRepository().save(session)

    from fretflow.coach import CoachService
    coach = CoachService()
    result = coach.analyse_runner(runner)
    print()
    print(coach.format_result(result))
    return 0








def _cmd_ear_train(args: argparse.Namespace) -> int:
    from fretflow.audio.reference_audio import ReferenceAudioEngine
    from fretflow.audio.sample_player import NullSink, default_sink
    from fretflow.coach.ear_training import EarExerciseKind, EarTrainingSession
    from fretflow.practice.fretboard import midi_to_preferred_position

    sink = default_sink() if args.play else NullSink()
    engine = ReferenceAudioEngine(sink=sink)
    session = EarTrainingSession(engine=engine)
    print("── Ear training ──")
    print("Le logiciel « pense » une note. Indice de position donné.")
    print("Dans cette démo CLI, la réponse correcte est révélée après écoute.\n")
    correct = 0
    for i in range(args.count):
        ch = session.next_challenge(EarExerciseKind.SINGLE_NOTE)
        session.play_prompt()
        midi = ch.primary_midi
        string, fret = midi_to_preferred_position(midi)
        print(f"  [{i+1}/{args.count}] {ch.prompt}")
        print(f"           → cible: MIDI {midi}  corde {string} case {fret}")
        # Auto-submit correct for demo when no interactive input
        result = session.submit(midi)
        if result.correct:
            correct += 1
            print("           OK")
        else:
            print("           Raté")
    print(f"\nScore: {correct}/{args.count} ({session.accuracy:.0%})")
    return 0

def _cmd_analyse_song(args: argparse.Namespace) -> int:
    from fretflow.coach.technique_detector import TechniqueDetector
    from fretflow.importers import import_song
    from fretflow.practice.fingering import FingeringEngine

    song = import_song(args.path)
    track = song.tracks[0] if song.tracks else None
    if track:
        assigned = FingeringEngine().assign_sequence(track.notes)
        # replace notes in first measure set for analysis
        if track.measures:
            track.measures[0].notes = assigned
    pedagogy = TechniqueDetector().analyse(song)
    print(f"── Analyse pedagogique : {song.title} ──")
    print(f"  Niveau estime  : {pedagogy.level.value}")
    print(f"  Duree indicative: {pedagogy.estimated_minutes:.0f} min")
    if pedagogy.techniques_summary:
        print("  Contenu :")
        for line in pedagogy.techniques_summary:
            print(f"    • {line}")
    if pedagogy.chord_names:
        print(f"  Accords : {', '.join(pedagogy.chord_names[:12])}")
    if pedagogy.tips:
        print("  Conseils :")
        for tip in pedagogy.tips:
            print(f"    → {tip}")
    return 0

def _cmd_progress(args: argparse.Namespace) -> int:
    import time
    from fretflow.profile.progress import ProgressService

    summary = ProgressService().summary(days=args.days)
    print(f"── Progression ({args.days} jours) ──")
    print(f"  Seances       : {summary.total_sessions}")
    print(f"  Minutes       : {summary.total_minutes:.1f}")
    print(f"  Precision moy : {summary.average_accuracy:.0%}")
    print(f"  Meilleur score: {summary.best_score}")
    if summary.last_session_at:
        print(f"  Derniere      : {time.strftime('%Y-%m-%d %H:%M', time.localtime(summary.last_session_at))}")
    if summary.days:
        print()
        print(f"  {'Jour':<12} {'Seances':>7} {'Min':>6} {'Prec.':>7}")
        for d in summary.days[-14:]:
            print(
                f"  {d.day.isoformat():<12} {d.session_count:>7} "
                f"{d.total_minutes:>6.1f} {d.average_accuracy:>6.0%}"
            )
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    from fretflow.profile.export import export_sessions_csv, export_sessions_json

    path = args.path
    if path.suffix.lower() == ".csv":
        out = export_sessions_csv(path, days=args.days)
    else:
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        out = export_sessions_json(path, days=args.days)
    print(f"Exporte vers {out}")
    return 0

def _cmd_coach(_args: argparse.Namespace) -> int:
    from fretflow.coach import CoachService, SkillProfile
    from fretflow.profile import SkillStore

    store = SkillStore()
    profile = store.load()
    service = CoachService(skill_store=store)

    print("── Skills ──")
    if not profile.levels:
        print("  Aucune donnee encore. Lancez : fretflow practice --auto")
    else:
        for skill in sorted(profile.levels.values(), key=lambda s: s.level):
            print(f"  {skill.label_fr:30} {skill.level:5.0%}  (n={skill.sample_count})")
    print()
    print("── Objectifs ──")
    for line in service.goals.summary_lines():
        print(f"  {line}")
    return 0

def _cmd_devices(_args: argparse.Namespace) -> int:
    from fretflow.audio import SimulatedCapture, SoundDeviceCapture

    print("Mode simulation : toujours disponible")
    print("  [simulated] default")
    try:
        real = SoundDeviceCapture()
        devices = real.list_devices()
        print(f"\nPériphériques sounddevice ({len(devices)}) :")
        for d in devices:
            print(f"  {d}")
    except Exception as exc:
        print(f"\nsounddevice indisponible : {exc}")
    return 0


def _cmd_diagnose_audio(args: argparse.Namespace) -> int:
    import numpy as np
    from fretflow.audio import YinDetector, hz_to_midi, midi_to_hz

    sr = 44100
    freq = args.freq
    t = np.arange(int(sr * 0.2)) / sr
    samples = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    det = YinDetector(noise_rms=0.001)
    est = det.detect(samples, sr, 0.0)
    print(f"Tone cible     : {freq:.2f} Hz (MIDI {hz_to_midi(freq):.2f})")
    if est is None:
        print("Détection     : échec")
        return 1
    print(f"Détecté        : {est.frequency_hz:.2f} Hz (MIDI {est.midi_pitch:.2f})")
    print(f"Confiance      : {est.confidence:.2f}")
    print(f"Cents          : {est.cents_offset:+.1f}")
    err = abs(est.frequency_hz - freq) / freq * 100
    print(f"Erreur relative: {err:.2f} %")
    return 0 if err < 5 else 1

def _cmd_ui(_args: argparse.Namespace) -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 n'est pas installé. Installez avec : pip install -e \".[ui]\"")
        return 1
    from fretflow.ui import MainWindow

    app = QApplication([])
    app.setApplicationName("FretFlow")
    win = MainWindow()
    win.show()
    return app.exec()

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    data_dir()
    config_dir()

    if args.init_config:
        path = write_default_config()
        print(f"Default config written to: {path}")
        return 0

    config = load_config()
    level_name = args.log_level or config.log_level
    level = getattr(logging, level_name, logging.INFO)
    setup_logging(level=level)
    logger.info("FretFlow %s starting", __version__)

    commands = {
        "scan": _cmd_scan,
        "library": _cmd_library,
        "import": _cmd_import,
        "practice": _cmd_practice,
        "history": _cmd_history,
        "ui": _cmd_ui,
        "coach": _cmd_coach,
        "ear-train": _cmd_ear_train,
        "analyse-song": _cmd_analyse_song,
        "progress": _cmd_progress,
        "export": _cmd_export,
        "devices": _cmd_devices,
        "diagnose-audio": _cmd_diagnose_audio,
    }
    if args.command in commands:
        return commands[args.command](args)

    print(f"FretFlow {__version__} — prêt.")
    print(f"  Données : {data_dir()}")
    print("  Milestone 2 (session & pratique) : OK")
    print()
    print("Commandes :")
    print("  fretflow scan <dossier>")
    print("  fretflow library")
    print("  fretflow import <fichier>")
    print("  fretflow practice [--auto] [--tempo 0.7] [fichier]")
    print("  fretflow history")
    print("  fretflow ui")
    return 0


if __name__ == "__main__":
    sys.exit(main())

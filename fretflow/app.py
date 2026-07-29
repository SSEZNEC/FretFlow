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

    report = runner.build_report()
    session = runner.build_session()
    SessionRepository().save(session)

    print()
    print("── Rapport de session ──")
    print(f"  Score     : {report.score}")
    print(f"  Précision : {report.accuracy:.0%}")
    print(f"  Hits/Miss : {report.notes_hit}/{report.notes_missed}")
    print(f"  Max combo : {report.max_combo}")
    print(f"  Offset moy: {report.average_offset_ms:+.1f} ms")
    for rec in report.recommendations:
        print(f"  → {rec}")
    return 0


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
    return 0


if __name__ == "__main__":
    sys.exit(main())

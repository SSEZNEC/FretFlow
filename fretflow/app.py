"""Composition root and application entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

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
    parser.add_argument(
        "--version",
        action="version",
        version=f"FretFlow {__version__}",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override log level from config",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Write a default config file and exit",
    )

    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Scan directories and import songs into the library")
    scan_p.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Directories to scan for .gp3/.gp4/.gp5/.mid files",
    )
    scan_p.add_argument(
        "--force",
        action="store_true",
        help="Re-import even if the file hash is unchanged",
    )

    sub.add_parser("library", help="List songs in the local library")

    import_p = sub.add_parser("import", help="Import a single song file")
    import_p.add_argument("file", type=Path, help="Path to a .mid / .gp3 / .gp4 / .gp5 file")

    return parser


def _cmd_scan(args: argparse.Namespace) -> int:
    from fretflow.library import LibraryScanner

    scanner = LibraryScanner()
    result = scanner.scan(args.paths, force=args.force)
    print(f"Importés : {result.imported}")
    print(f"Ignorés  : {result.skipped}")
    print(f"Échecs   : {result.failed}")
    for err in result.errors:
        print(f"  ! {err}")
    return 1 if result.failed and not result.imported else 0


def _cmd_library(_args: argparse.Namespace) -> int:
    from fretflow.library import SongRepository

    repo = SongRepository()
    songs = repo.list_songs()
    if not songs:
        print("Bibliothèque vide. Utilisez : fretflow scan <dossier>")
        return 0
    print(f"{'Titre':<40} {'Artiste':<20} {'BPM':>6} {'Durée':>8} {'Pistes':>6}")
    print("-" * 86)
    for s in songs:
        dur = float(s["duration_seconds"])
        print(
            f"{s['title'][:40]:<40} {s['artist'][:20]:<20} "
            f"{s['tempo_bpm']:>6.0f} {dur:>7.1f}s {s['track_count']:>6}"
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


def main(argv: list[str] | None = None) -> int:
    """Application entry point. Returns process exit code."""
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

    if args.command == "scan":
        return _cmd_scan(args)
    if args.command == "library":
        return _cmd_library(args)
    if args.command == "import":
        return _cmd_import(args)

    # Default: status banner (Milestone 0/1)
    print(f"FretFlow {__version__} — prêt.")
    print(f"  Données utilisateur : {data_dir()}")
    print(f"  Configuration       : {config_dir()}")
    print("  Milestone 1 (bibliothèque + import) : OK")
    print()
    print("Commandes :")
    print("  fretflow scan <dossier>   Importer les morceaux d'un dossier")
    print("  fretflow import <fichier> Importer un seul fichier")
    print("  fretflow library          Lister la bibliothèque")
    return 0


if __name__ == "__main__":
    sys.exit(main())

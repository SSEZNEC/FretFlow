"""Song importers (Guitar Pro, MIDI → internal Song model)."""

from __future__ import annotations

from pathlib import Path

from fretflow.core.errors import ImportError as FretFlowImportError
from fretflow.core.models import Song
from fretflow.importers.base import SUPPORTED_EXTENSIONS, SongImporter
from fretflow.importers.guitarpro import GuitarProImporter
from fretflow.importers.midi import MidiImporter

_IMPORTERS: list[SongImporter] = [
    GuitarProImporter(),
    MidiImporter(),
]


def get_importer(path: Path) -> SongImporter | None:
    """Return the first importer that can handle the given path."""
    path = Path(path)
    for importer in _IMPORTERS:
        if importer.can_import(path):
            return importer
    return None


def import_song(path: Path | str) -> Song:
    """Import a song file using the appropriate importer.

    Raises:
        ImportError: if the format is unsupported or parsing fails.
    """
    path = Path(path)
    importer = get_importer(path)
    if importer is None:
        raise FretFlowImportError(
            f"Unsupported format for {path.name} "
            f"(supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
        )
    return importer.import_song(path)


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "SongImporter",
    "GuitarProImporter",
    "MidiImporter",
    "get_importer",
    "import_song",
]

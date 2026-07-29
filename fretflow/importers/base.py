"""Importer protocol and registry."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from fretflow.core.models import Song


class SongImporter(Protocol):
    """Converts an external file into the internal Song model."""

    def can_import(self, path: Path) -> bool:
        """Return True if this importer supports the file."""
        ...

    def import_song(self, path: Path) -> Song:
        """Parse the file and return a Song. Raises ImportError on failure."""
        ...


SUPPORTED_EXTENSIONS = {".gp3", ".gp4", ".gp5", ".gpx", ".mid", ".midi"}

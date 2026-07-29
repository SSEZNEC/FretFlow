"""Scan directories for song files and import them into the library."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from fretflow.core.errors import ImportError as FretFlowImportError
from fretflow.importers import SUPPORTED_EXTENSIONS, import_song
from fretflow.library.repository import SongRepository, _file_hash

logger = logging.getLogger("fretflow.library.scanner")


@dataclass(slots=True)
class ScanResult:
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class LibraryScanner:
    """Walk directories and import supported song files."""

    def __init__(self, repository: SongRepository | None = None) -> None:
        self._repo = repository or SongRepository()

    def scan(self, roots: list[Path], *, force: bool = False) -> ScanResult:
        """Scan *roots* recursively for song files.

        If *force* is False, files already indexed with the same hash are skipped.
        """
        result = ScanResult()
        files: list[Path] = []
        for root in roots:
            root = Path(root)
            if not root.is_dir():
                result.errors.append(f"Not a directory: {root}")
                result.failed += 1
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(path)

        logger.info("Found %d candidate song file(s)", len(files))

        for path in files:
            try:
                if not force:
                    existing = self._repo.find_by_path(path.resolve())
                    if existing is not None:
                        try:
                            current_hash = _file_hash(path)
                        except OSError:
                            current_hash = None
                        if current_hash and existing.get("file_hash") == current_hash:
                            result.skipped += 1
                            continue

                song = import_song(path)
                self._repo.upsert_song(song)
                result.imported += 1
            except FretFlowImportError as exc:
                result.failed += 1
                result.errors.append(f"{path.name}: {exc}")
                logger.warning("Import failed for %s: %s", path, exc)
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"{path.name}: {exc}")
                logger.exception("Unexpected error importing %s", path)

        return result

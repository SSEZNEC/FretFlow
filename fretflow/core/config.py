"""Application configuration loaded from TOML."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fretflow.core.errors import ConfigurationError
from fretflow.core.paths import config_file_path

logger = logging.getLogger("fretflow.core.config")


@dataclass(slots=True)
class JudgmentWindows:
    """Timing windows in milliseconds relative to the expected note onset."""

    perfect_ms: float = 30.0
    great_ms: float = 60.0
    good_ms: float = 100.0


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration with sensible defaults."""

    language: str = "fr"
    theme: str = "dark"
    default_tempo_factor: float = 1.0
    judgment: JudgmentWindows = field(default_factory=JudgmentWindows)
    song_scan_dirs: list[str] = field(default_factory=list)
    log_level: str = "INFO"

    @classmethod
    def defaults(cls) -> AppConfig:
        return cls()


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from TOML, falling back to defaults."""
    config_path = path or config_file_path()
    if not config_path.exists():
        logger.info("No config file at %s — using defaults", config_path)
        return AppConfig.defaults()

    try:
        with config_path.open("rb") as fh:
            raw: dict[str, Any] = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(f"Cannot read config {config_path}: {exc}") from exc

    judgment_raw = raw.get("judgment", {})
    judgment = JudgmentWindows(
        perfect_ms=float(judgment_raw.get("perfect_ms", 30.0)),
        great_ms=float(judgment_raw.get("great_ms", 60.0)),
        good_ms=float(judgment_raw.get("good_ms", 100.0)),
    )

    return AppConfig(
        language=str(raw.get("language", "fr")),
        theme=str(raw.get("theme", "dark")),
        default_tempo_factor=float(raw.get("default_tempo_factor", 1.0)),
        judgment=judgment,
        song_scan_dirs=[str(p) for p in raw.get("song_scan_dirs", [])],
        log_level=str(raw.get("log_level", "INFO")).upper(),
    )


def write_default_config(path: Path | None = None) -> Path:
    """Write a default TOML config if none exists. Returns the path written."""
    config_path = path or config_file_path()
    if config_path.exists():
        return config_path

    content = """\
# FretFlow configuration

language = "fr"
theme = "dark"
default_tempo_factor = 1.0
log_level = "INFO"

# Directories to scan for song files (Guitar Pro, MIDI)
song_scan_dirs = []

[judgment]
perfect_ms = 30.0
great_ms = 60.0
good_ms = 100.0
"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    logger.info("Wrote default config to %s", config_path)
    return config_path

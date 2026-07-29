"""User data directories (local-first)."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "FretFlow"
APP_AUTHOR = "SSEZNEC"


def data_dir() -> Path:
    """Return the platform-specific user data directory and ensure it exists."""
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    """Return the platform-specific user config directory and ensure it exists."""
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def library_db_path() -> Path:
    """SQLite database for the song library and sessions."""
    return data_dir() / "library.db"


def config_file_path() -> Path:
    """TOML configuration file path."""
    return config_dir() / "config.toml"

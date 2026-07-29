"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from fretflow.core.config import AppConfig, load_config, write_default_config
from fretflow.core.errors import ConfigurationError


def test_defaults() -> None:
    cfg = AppConfig.defaults()
    assert cfg.language == "fr"
    assert cfg.judgment.perfect_ms == 30.0


def test_write_and_load_default(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    write_default_config(path)
    assert path.exists()
    cfg = load_config(path)
    assert cfg.theme == "dark"
    assert cfg.judgment.good_ms == 100.0


def test_load_missing_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.toml"
    cfg = load_config(path)
    assert cfg.language == "fr"


def test_load_invalid_toml_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("this is not = valid [[ toml", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(path)


def test_custom_judgment_values(tmp_path: Path) -> None:
    path = tmp_path / "custom.toml"
    path.write_text(
        """
language = "en"
[judgment]
perfect_ms = 20.0
great_ms = 50.0
good_ms = 90.0
""",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.language == "en"
    assert cfg.judgment.perfect_ms == 20.0
    assert cfg.judgment.great_ms == 50.0

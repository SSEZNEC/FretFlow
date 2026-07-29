"""Smoke tests for the application entry point."""

from __future__ import annotations

import pytest

from fretflow import __version__
from fretflow.app import main


def test_main_returns_zero() -> None:
    assert main([]) == 0


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out

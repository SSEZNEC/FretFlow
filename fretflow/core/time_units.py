"""Explicit time unit conversions.

Internal time is always float seconds.
Display offsets use milliseconds.
"""

from __future__ import annotations


def seconds_to_ms(seconds: float) -> float:
    """Convert seconds to milliseconds."""
    return seconds * 1000.0


def ms_to_seconds(milliseconds: float) -> float:
    """Convert milliseconds to seconds."""
    return milliseconds / 1000.0

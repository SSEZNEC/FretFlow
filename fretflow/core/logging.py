"""Structured logging setup for FretFlow."""

from __future__ import annotations

import logging
import sys
from typing import TextIO


def setup_logging(
    level: int = logging.INFO,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure the root FretFlow logger and return it.

    Application code must use ``logging.getLogger("fretflow...")``
    and never call ``print()``.
    """
    logger = logging.getLogger("fretflow")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger

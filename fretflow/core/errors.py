"""Domain-specific exceptions for FretFlow."""

from __future__ import annotations


class FretFlowError(Exception):
    """Base exception for all FretFlow domain errors."""


class ImportError(FretFlowError):
    """Raised when a song file cannot be imported or parsed."""


class PersistenceError(FretFlowError):
    """Raised when reading or writing local data fails."""


class ConfigurationError(FretFlowError):
    """Raised when configuration is invalid or missing."""


class AudioDeviceError(FretFlowError):
    """Raised when an audio device cannot be opened or used."""


class JudgmentError(FretFlowError):
    """Raised when judgment parameters are inconsistent."""

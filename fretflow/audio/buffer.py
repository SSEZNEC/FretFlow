"""Circular audio buffer (pre-allocated, safe for tests)."""

from __future__ import annotations

import numpy as np


class CircularBuffer:
    """Fixed-capacity mono float32 ring buffer."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._buf = np.zeros(capacity, dtype=np.float32)
        self._capacity = capacity
        self._write = 0
        self._filled = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def filled(self) -> int:
        return self._filled

    def write(self, samples: np.ndarray) -> None:
        samples = np.asarray(samples, dtype=np.float32).ravel()
        n = samples.size
        if n == 0:
            return
        if n >= self._capacity:
            self._buf[:] = samples[-self._capacity :]
            self._write = 0
            self._filled = self._capacity
            return
        end = self._write + n
        if end <= self._capacity:
            self._buf[self._write : end] = samples
        else:
            first = self._capacity - self._write
            self._buf[self._write :] = samples[:first]
            self._buf[: n - first] = samples[first:]
        self._write = (self._write + n) % self._capacity
        self._filled = min(self._capacity, self._filled + n)

    def read_latest(self, n: int) -> np.ndarray:
        """Return the last *n* samples in chronological order."""
        n = min(n, self._filled)
        if n == 0:
            return np.zeros(0, dtype=np.float32)
        start = (self._write - n) % self._capacity
        if start + n <= self._capacity:
            return self._buf[start : start + n].copy()
        first = self._capacity - start
        return np.concatenate([self._buf[start:], self._buf[: n - first]])

    def clear(self) -> None:
        self._buf[:] = 0
        self._write = 0
        self._filled = 0

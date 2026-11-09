"""Rozwijanie fazy (phase unwrap) — własna implementacja."""
from __future__ import annotations

import numpy as np


def unwrap_phase(p, discont: float = np.pi, axis: int = -1) -> np.ndarray:
    """Usuwa skoki fazy większe niż `discont`, dodając wielokrotności 2π."""
    p = np.asarray(p, dtype=float)
    d = np.diff(p, axis=axis)
    dm = np.mod(d + np.pi, 2 * np.pi) - np.pi
    dm[(dm == -np.pi) & (d > 0)] = np.pi
    corr = dm - d
    corr[np.abs(d) < discont] = 0.0
    out = p.copy()
    sl = [slice(None)] * p.ndim
    sl[axis] = slice(1, None)
    out[tuple(sl)] = p[tuple(sl)] + np.cumsum(corr, axis=axis)
    return out

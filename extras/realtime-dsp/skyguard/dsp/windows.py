"""Okna czasowe (własna implementacja, wzory z literatury: Harris 1978)."""
from __future__ import annotations

import numpy as np


def _n(n: int, sym: bool) -> np.ndarray:
    if n < 1:
        raise ValueError("n musi być >= 1")
    if n == 1:
        return np.zeros(1)
    m = n - 1 if sym else n
    return np.arange(n) / m


def _cosine_sum(n: int, coeffs, sym: bool) -> np.ndarray:
    if n == 1:
        return np.ones(1)
    x = 2 * np.pi * _n(n, sym)
    w = np.zeros(n)
    for k, a in enumerate(coeffs):
        w += ((-1) ** k) * a * np.cos(k * x)
    return w


def hann(n: int, sym: bool = False) -> np.ndarray:
    return _cosine_sum(n, (0.5, 0.5), sym)


def hamming(n: int, sym: bool = False) -> np.ndarray:
    return _cosine_sum(n, (0.54, 0.46), sym)


def blackman(n: int, sym: bool = False) -> np.ndarray:
    return _cosine_sum(n, (0.42, 0.5, 0.08), sym)


def blackman_harris(n: int, sym: bool = False) -> np.ndarray:
    return _cosine_sum(n, (0.35875, 0.48829, 0.14128, 0.01168), sym)


def kaiser(n: int, beta: float = 8.6, sym: bool = False) -> np.ndarray:
    if n == 1:
        return np.ones(1)
    m = n - 1 if sym else n
    k = np.arange(n)
    r = 2.0 * k / m - 1.0
    return np.i0(beta * np.sqrt(np.clip(1 - r * r, 0, None))) / np.i0(beta)


_WINDOWS = {
    "hann": hann, "hanning": hann, "hamming": hamming,
    "blackman": blackman, "blackmanharris": blackman_harris,
    "blackman_harris": blackman_harris, "kaiser": kaiser,
    "rect": lambda n, sym=False: np.ones(n), "boxcar": lambda n, sym=False: np.ones(n),
}


def get_window(name: str, n: int, sym: bool = False) -> np.ndarray:
    try:
        return _WINDOWS[name.lower()](n, sym=sym)
    except KeyError as e:
        raise ValueError(f"nieznane okno: {name}") from e

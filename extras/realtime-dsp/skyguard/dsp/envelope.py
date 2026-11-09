"""Sygnał analityczny i obwiednia Hilberta (metoda FFT, Marple 1999)."""
from __future__ import annotations

import numpy as np


def analytic_signal(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n = x.shape[-1]
    X = np.fft.fft(x, axis=-1)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    return np.fft.ifft(X * h, axis=-1)


def hilbert_envelope(x) -> np.ndarray:
    return np.abs(analytic_signal(x))

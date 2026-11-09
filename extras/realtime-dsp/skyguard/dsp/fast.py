"""Szybkie jądra DSP z numba (JIT). Gdy numba brak — fallback numpy."""
from __future__ import annotations

import numpy as np

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except Exception:  # pragma: no cover
    NUMBA_AVAILABLE = False

    def njit(*a, **k):
        if a and callable(a[0]):
            return a[0]
        return lambda f: f


@njit(cache=True, fastmath=True)
def frame_energy(iq: np.ndarray) -> float:
    """Średnia moc ramki zespolonej I/Q (|x|^2)."""
    acc = 0.0
    for i in range(iq.shape[0]):
        acc += iq[i].real * iq[i].real + iq[i].imag * iq[i].imag
    return acc / iq.shape[0]


def frame_spectrum_energy(iq: np.ndarray, window: np.ndarray | None = None):
    """FFT ramki I/Q -> (widmo mocy, energia, indeks piku)."""
    w = window if window is not None else np.ones(iq.shape[0])
    spec = np.fft.fftshift(np.abs(np.fft.fft(iq * w)) ** 2) / iq.shape[0]
    return spec, frame_energy(iq), int(np.argmax(spec))

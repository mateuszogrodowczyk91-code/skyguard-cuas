# Copyright 2019 The OpenRadar Authors (PreSenseRadar/OpenRadar)
# SPDX-License-Identifier: Apache-2.0
#
# Zaadaptowane z mmwave/dsp/compensation.py (clutter_removal: odjęcie średniej
# po osi chirpów). Zmiany SKYGUARD: dowolna oś bez transpozycji; dodane
# (własne) filtr MTI 2/3-impulsowy, wykładnicza średnia tła i FFT kątowe. Licencja: THIRD_PARTY_LICENSES.md.
"""Usuwanie ech stałych (clutter), MTI i FFT kątowe dla kostki radarowej."""
from __future__ import annotations

import numpy as np


def clutter_removal(cube: np.ndarray, axis: int = 0) -> np.ndarray:
    """Odejmuje średnią po osi chirpów (obiekty nieruchome → 0)."""
    return cube - cube.mean(axis=axis, keepdims=True)


def mti_filter(chirps: np.ndarray, taps: int = 2, axis: int = 0) -> np.ndarray:
    """Kanceler 2-impulsowy [1,-1] lub 3-impulsowy [1,-2,1] po osi chirpów."""
    c = np.moveaxis(np.asarray(chirps), axis, 0)
    if taps == 2:
        y = c[1:] - c[:-1]
    elif taps == 3:
        y = c[2:] - 2 * c[1:-1] + c[:-2]
    else:
        raise ValueError("taps: 2 lub 3")
    return np.moveaxis(y, 0, axis)


class BackgroundSubtractor:
    """Średnia wykładnicza tła dla kolejnych ramek range-profile."""

    def __init__(self, alpha: float = 0.05):
        self.alpha, self.bg = alpha, None

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        if self.bg is None:
            self.bg = np.array(frame, dtype=complex)
        out = frame - self.bg
        self.bg = (1 - self.alpha) * self.bg + self.alpha * frame
        return out


def angle_fft(x: np.ndarray, n_fft: int = 64, axis: int = -1) -> tuple[np.ndarray, np.ndarray]:
    """FFT kątowe po antenach (d = λ/2). Zwraca (kąty[°], |widmo|)."""
    S = np.fft.fftshift(np.fft.fft(x, n_fft, axis=axis), axes=axis)
    u = np.fft.fftshift(np.fft.fftfreq(n_fft)) * 2  # sinθ = 2·f_norm dla d=λ/2
    return np.degrees(np.arcsin(np.clip(u, -1, 1))), np.abs(S)

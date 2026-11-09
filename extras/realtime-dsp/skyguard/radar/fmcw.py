"""Przetwarzanie FMCW: FFT zakresu i Dopplera."""
from __future__ import annotations

import numpy as np

from ..dsp.windows import hann

C = 299_792_458.0


def range_fft(chirps, n_fft: int | None = None, window=True) -> np.ndarray:
    """chirps: (n_chirps, n_samples) -> widmo zespolone zakresu."""
    c = np.asarray(chirps)
    ns = c.shape[-1]
    w = hann(ns) if window else 1.0
    return np.fft.fft(c * w, n=n_fft or ns, axis=-1)


def range_doppler_map(chirps, window=True) -> np.ndarray:
    """Mapa MOCY range-Doppler (n_doppler, n_range), Doppler przesunięty fftshift."""
    r = range_fft(chirps, window=window)
    nc = r.shape[0]
    w = hann(nc)[:, None] if window else 1.0
    rd = np.fft.fftshift(np.fft.fft(r * w, axis=0), axes=0)
    return np.abs(rd) ** 2


def range_axis(n_samples: int, fs: float, slope_hz_per_s: float) -> np.ndarray:
    f_beat = np.arange(n_samples) * fs / n_samples
    return f_beat * C / (2 * slope_hz_per_s)


def velocity_axis(n_chirps: int, chirp_period_s: float, fc_hz: float) -> np.ndarray:
    lam = C / fc_hz
    fd = (np.arange(n_chirps) - n_chirps // 2) / (n_chirps * chirp_period_s)
    return fd * lam / 2

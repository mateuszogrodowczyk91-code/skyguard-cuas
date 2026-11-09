"""Banki filtrów: LFCC (liniowe cepstrum) i gammatone (Patterson/Slaney ERB)."""
from __future__ import annotations

import numpy as np

from .windows import hamming


def _dct2_ortho(x: np.ndarray, n_out: int) -> np.ndarray:
    n = x.shape[-1]
    k = np.arange(n_out)[:, None]
    m = np.arange(n)[None, :]
    basis = np.cos(np.pi * k * (2 * m + 1) / (2 * n))
    scale = np.full(n_out, np.sqrt(2.0 / n))
    scale[0] = np.sqrt(1.0 / n)
    return (x @ basis.T) * scale


def lfcc(x, sr: int, n_fft: int = 1024, hop: int = 512, n_filters: int = 40,
         n_coeffs: int = 20, fmin: float = 0.0, fmax: float | None = None) -> np.ndarray:
    """Linear-Frequency Cepstral Coefficients, kształt (ramki, n_coeffs)."""
    x = np.asarray(x, dtype=float)
    fmax = fmax or sr / 2
    if x.size < n_fft:
        x = np.pad(x, (0, n_fft - x.size))
    k = 1 + (x.size - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(k)[:, None]
    P = np.abs(np.fft.rfft(x[idx] * hamming(n_fft), axis=1)) ** 2
    freqs = np.linspace(0, sr / 2, P.shape[1])
    edges = np.linspace(fmin, fmax, n_filters + 2)
    fb = np.zeros((n_filters, P.shape[1]))
    for i in range(n_filters):
        lo, c, hi = edges[i], edges[i + 1], edges[i + 2]
        up = (freqs - lo) / (c - lo)
        dn = (hi - freqs) / (hi - c)
        fb[i] = np.clip(np.minimum(up, dn), 0, None)
    E = np.log(P @ fb.T + 1e-10)
    return _dct2_ortho(E, n_coeffs)


def erb_space(fmin: float, fmax: float, n: int) -> np.ndarray:
    """n częstotliwości środkowych równomiernie w skali ERB (Glasberg & Moore)."""
    ear_q, min_bw = 9.26449, 24.7
    a = ear_q * min_bw
    lo, hi = np.log(fmin + a), np.log(fmax + a)
    return np.exp(np.linspace(lo, hi, n)) - a


def gammatone_filterbank(x, sr: int, n_bands: int = 32, fmin: float = 50.0,
                         fmax: float | None = None, order: int = 4,
                         dur: float = 0.064) -> tuple[np.ndarray, np.ndarray]:
    """Bank filtrów gammatone (odpowiedzi impulsowe FIR, splot przez FFT).

    Zwraca (cf, y) gdzie y ma kształt (n_bands, len(x))."""
    x = np.asarray(x, dtype=float)
    fmax = fmax or 0.9 * sr / 2
    cf = erb_space(fmin, fmax, n_bands)
    t = np.arange(int(dur * sr)) / sr
    nfft = 1 << int(np.ceil(np.log2(x.size + t.size - 1)))
    X = np.fft.rfft(x, nfft)
    y = np.empty((n_bands, x.size))
    for i, f in enumerate(cf):
        erb = 24.7 + f / 9.26449
        b = 1.019 * erb
        g = t ** (order - 1) * np.exp(-2 * np.pi * b * t) * np.cos(2 * np.pi * f * t)
        G = np.fft.rfft(g, nfft)
        g /= np.max(np.abs(G)) + 1e-20  # wzmocnienie 0 dB na cf
        y[i] = np.fft.irfft(X * np.fft.rfft(g, nfft), nfft)[:x.size]
    return cf, y

"""Cechy sygnału: Teager-Kaiser, Hjorth, odejmowanie widmowe, TSA."""
from __future__ import annotations

import numpy as np


def teager_kaiser(x) -> np.ndarray:
    """Operator energii Teagera-Kaisera: psi[n] = x[n]^2 - x[n-1]*x[n+1].

    Brzegi uzupełnione wartościami sąsiednimi (ta sama długość co wejście)."""
    x = np.asarray(x, dtype=float)
    if x.size < 3:
        return np.zeros_like(x)
    psi = np.empty_like(x)
    psi[1:-1] = x[1:-1] ** 2 - x[:-2] * x[2:]
    psi[0], psi[-1] = psi[1], psi[-2]
    return psi


def hjorth(x) -> tuple[float, float, float]:
    """Parametry Hjortha: (activity, mobility, complexity)."""
    x = np.asarray(x, dtype=float)
    dx = np.diff(x)
    ddx = np.diff(dx)
    v0, v1, v2 = np.var(x), np.var(dx), np.var(ddx)
    if v0 == 0 or v1 == 0:
        return float(v0), 0.0, 0.0
    mob = np.sqrt(v1 / v0)
    comp = np.sqrt(v2 / v1) / mob
    return float(v0), float(mob), float(comp)


def spectral_subtraction(x, noise, n_fft: int = 1024, hop: int | None = None,
                         alpha: float = 2.0, floor: float = 0.02) -> np.ndarray:
    """Odejmowanie widmowe (Boll 1979, z nadodejmowaniem Berouti 1979).

    `noise` — fragment samego tła; zwraca odszumiony sygnał tej samej długości."""
    from .windows import hann
    x = np.asarray(x, dtype=float)
    noise = np.asarray(noise, dtype=float)
    hop = hop or n_fft // 2
    w = hann(n_fft)

    def frames(sig):
        if sig.size < n_fft:
            sig = np.pad(sig, (0, n_fft - sig.size))
        k = 1 + (sig.size - n_fft) // hop
        idx = np.arange(n_fft)[None, :] + hop * np.arange(k)[:, None]
        return sig[idx] * w

    noise_pow = np.mean(np.abs(np.fft.rfft(frames(noise), axis=1)) ** 2, axis=0)
    # dopełnienie z obu stron, żeby brzegi miały pełne pokrycie oknami (COLA)
    tail = n_fft + (-(x.size + n_fft) % hop)
    xp = np.pad(x, (n_fft, tail))
    F = np.fft.rfft(frames(xp), axis=1)
    p = np.abs(F) ** 2
    clean = np.maximum(p - alpha * noise_pow, floor * p)
    Y = np.sqrt(clean) * np.exp(1j * np.angle(F))
    y_fr = np.fft.irfft(Y, n=n_fft, axis=1) * w
    out = np.zeros(xp.size)
    norm = np.zeros(xp.size)
    for i, fr in enumerate(y_fr):
        out[i * hop:i * hop + n_fft] += fr
        norm[i * hop:i * hop + n_fft] += w ** 2
    out /= np.maximum(norm, 1e-3)
    return out[n_fft:n_fft + x.size]


def tsa(x, period_samples: float, n_periods: int | None = None) -> np.ndarray:
    """Time Synchronous Averaging — uśrednienie po okresie obrotu (np. śmigła).

    Okres może być ułamkowy (interpolacja liniowa). Zwraca jeden uśredniony okres."""
    x = np.asarray(x, dtype=float)
    L = int(round(period_samples))
    if L < 2:
        raise ValueError("okres za krótki")
    k_max = int((x.size - 1) // period_samples)
    k = min(k_max, n_periods) if n_periods else k_max
    if k < 1:
        raise ValueError("sygnał krótszy niż jeden okres")
    t = np.arange(L) * (period_samples / L)
    acc = np.zeros(L)
    grid = np.arange(x.size)
    for i in range(k):
        acc += np.interp(i * period_samples + t, grid, x)
    return acc / k

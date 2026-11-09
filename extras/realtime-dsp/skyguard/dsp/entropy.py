"""Miary złożoności sygnału: entropia widmowa, permutacyjna, wymiar Higuchiego.

Zaadaptowane z raphaelvallat/antropy (BSD-3-Clause, © 2018-2021 Raphael Vallat):
spectral_entropy (Welch, normalizacja log2(N)), perm_entropy (Bandt-Pompe),
higuchi_fd. Zmiany SKYGUARD: czysty numpy (bez numba), API pod okna 1 s.
Ton drona = niska entropia widmowa; szum wiatru/deszczu = wysoka."""
from __future__ import annotations

import math

import numpy as np
from scipy.signal import welch


def spectral_entropy(x, sr: int, nperseg: int | None = None, normalize: bool = True,
                     fmin: float = 0.0, fmax: float | None = None) -> float:
    f, p = welch(np.asarray(x, float), sr, nperseg=nperseg or min(1024, len(x)))
    sel = (f >= fmin) & (f <= (fmax or sr / 2))
    p = p[sel]
    s = p.sum()
    if s <= 0:
        return 0.0
    p = p / s
    h = -np.sum(p[p > 0] * np.log2(p[p > 0]))
    return float(h / np.log2(p.size) if normalize else h)


def perm_entropy(x, order: int = 3, delay: int = 1, normalize: bool = True) -> float:
    x = np.asarray(x, float)
    n = x.size - (order - 1) * delay
    if n <= 0:
        raise ValueError("sygnał za krótki")
    emb = np.stack([x[i * delay:i * delay + n] for i in range(order)], axis=1)
    ranks = np.argsort(emb, kind="quicksort", axis=1)
    codes = (ranks * (order ** np.arange(order))).sum(axis=1)
    _, c = np.unique(codes, return_counts=True)
    p = c / c.sum()
    h = -np.sum(p * np.log2(p))
    return float(h / np.log2(math.factorial(order)) if normalize else h)


def higuchi_fd(x, kmax: int = 10) -> float:
    x = np.asarray(x, float)
    N = x.size
    lk = []
    ks = np.arange(1, kmax + 1)
    for k in ks:
        lm = []
        for m in range(k):
            idx = np.arange(m, N, k)
            if idx.size < 2:
                continue
            lmk = np.abs(np.diff(x[idx])).sum() * (N - 1) / ((idx.size - 1) * k) / k
            lm.append(lmk)
        lk.append(np.mean(lm))
    slope = np.polyfit(np.log(1.0 / ks), np.log(lk), 1)[0]
    return float(slope)

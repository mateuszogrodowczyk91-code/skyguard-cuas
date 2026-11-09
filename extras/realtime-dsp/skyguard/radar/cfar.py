"""CFAR (Constant False Alarm Rate): CA, GO, SO (CASO), OS — własna implementacja.

Wzory progów: Richards, "Fundamentals of Radar Signal Processing", rozdz. 6."""
from __future__ import annotations

import numpy as np


def _ca_alpha(n: int, pfa: float) -> float:
    return n * (pfa ** (-1.0 / n) - 1.0)


def cfar_1d(x, guard: int = 2, train: int = 8, pfa: float = 1e-4,
            method: str = "ca", os_rank: float = 0.75) -> tuple[np.ndarray, np.ndarray]:
    """CFAR na wektorze MOCY (|x|^2). Zwraca (maska detekcji, próg).

    method: 'ca' (średnia), 'go' (większa z połówek), 'so'/'caso' (mniejsza),
    'os' (statystyka pozycyjna, ranga os_rank * 2*train)."""
    p = np.asarray(x, dtype=float)
    n = p.size
    m = method.lower()
    if m == "caso":
        m = "so"
    N = 2 * train
    if m == "ca":
        alpha = _ca_alpha(N, pfa)
    elif m in ("go", "so"):
        alpha = _ca_alpha(train, pfa)  # przybliżenie (połowa okna)
    elif m == "os":
        alpha = _ca_alpha(N, pfa)  # przybliżenie; OS-ranga na rozkładzie wykładniczym
    else:
        raise ValueError(f"nieznana metoda CFAR: {method}")
    thr = np.full(n, np.inf)
    k = int(np.clip(round(os_rank * N), 1, N)) - 1
    for i in range(train + guard, n - train - guard):
        lead = p[i - guard - train:i - guard]
        lag = p[i + guard + 1:i + guard + 1 + train]
        if m == "ca":
            z = (lead.sum() + lag.sum()) / N
        elif m == "go":
            z = max(lead.mean(), lag.mean())
        elif m == "so":
            z = min(lead.mean(), lag.mean())
        else:
            z = np.partition(np.concatenate([lead, lag]), k)[k]
        thr[i] = alpha * z
    return p > thr, thr


def cfar_2d(rd, guard=(2, 2), train=(8, 4), pfa: float = 1e-5) -> np.ndarray:
    """CA-CFAR 2D na mapie mocy range-Doppler (szybko: sumy przez splot FFT)."""
    from scipy.signal import fftconvolve
    p = np.asarray(rd, dtype=float)
    gr, gd = guard
    tr, td = train
    outer = np.ones((2 * (gr + tr) + 1, 2 * (gd + td) + 1))
    inner = np.zeros_like(outer)
    inner[tr:tr + 2 * gr + 1, td:td + 2 * gd + 1] = 1
    kern = outer - inner
    n = kern.sum()
    noise = fftconvolve(p, kern, mode="same") / n
    alpha = _ca_alpha(int(n), pfa)
    mask = p > alpha * noise
    mask[:gr + tr, :] = mask[-(gr + tr):, :] = False
    mask[:, :gd + td] = mask[:, -(gd + td):] = False
    return mask

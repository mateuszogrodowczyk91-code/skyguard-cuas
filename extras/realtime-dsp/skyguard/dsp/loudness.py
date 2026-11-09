"""Głośność wg ITU-R BS.1770-4 / EBU R128 (LUFS) i normalizacja.

Zaadaptowane z csteinmetz1/pyloudnorm (MIT, © 2018 Christian Steinmetz):
filtry K-weighting (high-shelf 4 dB @1500 Hz, Q=1/√2 + high-pass 38 Hz, Q=0.5,
biquady RBJ), bloki 400 ms z 75% nakładaniem, bramka absolutna −70 LUFS
i względna −10 LU. Zmiany SKYGUARD: tylko mono/stereo, wektorowe bloki,
`normalize()` z ochroną przed przesterowaniem (sufit −1 dBFS)."""
from __future__ import annotations

import numpy as np
from scipy.signal import lfilter


def _biquad(kind, G, Q, fc, sr):
    A = 10 ** (G / 40.0)
    w0 = 2 * np.pi * fc / sr
    alpha = np.sin(w0) / (2 * Q)
    c = np.cos(w0)
    if kind == "high_shelf":
        b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * alpha), -2 * A * ((A - 1) + (A + 1) * c),
             A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * alpha)]
        a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * alpha, 2 * ((A - 1) - (A + 1) * c),
             (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * alpha]
    elif kind == "high_pass":
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
        a = [1 + alpha, -2 * c, 1 - alpha]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def k_weight(x, sr: int) -> np.ndarray:
    for kind, G, Q, fc in (("high_shelf", 4.0, 1 / np.sqrt(2), 1500.0), ("high_pass", 0.0, 0.5, 38.0)):
        b, a = _biquad(kind, G, Q, fc, sr)
        x = lfilter(b, a, x, axis=0)
    return x


def integrated_loudness(x, sr: int, block_s: float = 0.4, overlap: float = 0.75) -> float:
    """Zintegrowana głośność w LUFS (−inf dla ciszy)."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    y = k_weight(x, sr)
    n_blk = int(round(block_s * sr))
    step = int(round(n_blk * (1 - overlap)))
    if y.shape[0] < n_blk:
        return float("-inf")
    starts = np.arange(0, y.shape[0] - n_blk + 1, step)
    z = np.array([np.mean(y[s:s + n_blk] ** 2, axis=0) for s in starts])  # (bloki, kanały)
    zs = z.sum(axis=1)
    with np.errstate(divide="ignore"):
        lj = -0.691 + 10 * np.log10(zs)
    g = lj >= -70.0
    if not g.any():
        return float("-inf")
    gamma_r = -0.691 + 10 * np.log10(zs[g].mean()) - 10.0
    g2 = g & (lj > gamma_r)
    return float(-0.691 + 10 * np.log10(zs[g2].mean()))


def normalize(x, sr: int, target_lufs: float = -23.0, peak_ceiling_dbfs: float = -1.0) -> np.ndarray:
    """Normalizuje do `target_lufs`, ale nigdy nie przekracza sufitu szczytowego."""
    x = np.asarray(x, dtype=float)
    L = integrated_loudness(x, sr)
    if not np.isfinite(L):
        return x.copy()
    g = 10 ** ((target_lufs - L) / 20)
    peak = np.max(np.abs(x)) * g
    ceil = 10 ** (peak_ceiling_dbfs / 20)
    if peak > ceil:
        g *= ceil / peak
    return x * g

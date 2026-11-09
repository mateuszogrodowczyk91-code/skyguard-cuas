"""Śledzenie tonu śmigieł: wybielony grzebień harmonicznych + Viterbi + liczenie wirników.

Metody (własna implementacja — repozytoria źródłowe nie mają licencji albo
mają licencję niestandardową, więc kodu NIE kopiowano):
- Quailworker/audiodrone: grzebień harmonicznych + ścieżka Viterbiego f0
  (ciągłość tonu w czasie odróżnia silnik od przypadkowych pików),
- agamrossen/VolAnti: wynik grzebienia na widmie wybielonym (medianą),
- poglesbyg/huginn: liczenie dronów jako liczby rozłącznych „rodzin” f0.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import median_filter

from .mel import stft_power


def whitened_spectrogram(x, sr: int, n_fft: int = 4096, hop: int = 1024, med_hz: float = 150.0):
    P = stft_power(x, n_fft, hop)
    f = np.linspace(0, sr / 2, P.shape[0])
    k = max(3, int(med_hz / (sr / n_fft)) | 1)
    floor = median_filter(P, size=(k, 1), mode="nearest") + 1e-12
    return f, np.log(P / floor + 1e-12).clip(min=0)


def comb_salience(W: np.ndarray, f: np.ndarray, f0_grid, n_harm: int = 8) -> np.ndarray:
    """Salience(f0, t) = średnia z wybielonego widma w n_harm harmonicznych (waga 1/sqrt(h))."""
    df = f[1] - f[0]
    S = np.zeros((len(f0_grid), W.shape[1]))
    for i, f0 in enumerate(f0_grid):
        acc, wsum = 0.0, 0.0
        for h in range(1, n_harm + 1):
            b = int(round(h * f0 / df))
            if b >= W.shape[0] - 1:
                break
            wgt = 1 / np.sqrt(h)
            acc = acc + wgt * W[max(b - 1, 0):b + 2].max(axis=0)
            wsum += wgt
        if wsum:
            S[i] = acc / wsum
    return S


def viterbi_track(S: np.ndarray, max_jump: int = 3, jump_cost: float = 0.3) -> np.ndarray:
    """Najlepsza ścieżka indeksów f0 maksymalizująca sumę salience − koszt skoków."""
    n_f, n_t = S.shape
    score = S[:, 0].copy()
    back = np.zeros((n_f, n_t), int)
    offs = np.arange(-max_jump, max_jump + 1)
    for t in range(1, n_t):
        best = np.full(n_f, -np.inf)
        arg = np.zeros(n_f, int)
        for o in offs:
            src = np.clip(np.arange(n_f) - o, 0, n_f - 1)
            cand = score[src] - jump_cost * abs(o)
            m = cand > best
            best[m] = cand[m]
            arg[m] = src[m]
        score = best + S[:, t]
        back[:, t] = arg
    path = np.zeros(n_t, int)
    path[-1] = int(np.argmax(score))
    for t in range(n_t - 1, 0, -1):
        path[t - 1] = back[path[t], t]
    return path


@dataclass
class HarmonicReport:
    f0_hz: float            # mediana f0 ścieżki
    salience: float         # średnia siła grzebienia na ścieżce
    stability: float        # 0..1, ułamek ramek, gdzie f0 zmienia się o ≤ 2 kroki siatki
    track_hz: np.ndarray    # f0 w czasie
    n_rotor_families: int   # ile rozłącznych rodzin tonów (≈ ile dronów)


def analyze_harmonics(x, sr: int, fmin: float = 60.0, fmax: float = 600.0, n_f0: int = 180,
                      n_fft: int = 4096, hop: int = 1024) -> HarmonicReport:
    f, W = whitened_spectrogram(x, sr, n_fft, hop)
    grid = np.geomspace(fmin, fmax, n_f0)
    S = comb_salience(W, f, grid)
    path = viterbi_track(S)
    track = grid[path]
    sal = float(np.mean(S[path, np.arange(S.shape[1])]))
    stab = float(np.mean(np.abs(np.diff(path)) <= 2)) if path.size > 1 else 0.0
    fam = count_rotor_families(S, grid)
    return HarmonicReport(float(np.median(track)), sal, stab, track, fam)


def count_rotor_families(S: np.ndarray, grid, rel_thr: float = 0.6, min_sep_ratio: float = 1.08) -> int:
    """Liczba rozłącznych tonów podstawowych (nie będących harmonicznymi siebie nawzajem)."""
    prof = S.mean(axis=1)
    if prof.max() <= 0:
        return 0
    pk = np.where((prof[1:-1] > prof[:-2]) & (prof[1:-1] >= prof[2:]) & (prof[1:-1] > rel_thr * prof.max()))[0] + 1
    fams: list[float] = []
    for i in pk[np.argsort(prof[pk])[::-1]]:
        f0 = grid[i]
        related = False
        for g in fams:
            r = max(f0, g) / min(f0, g)
            if abs(r - round(r)) < 0.04 * round(r) or r < min_sep_ratio:
                related = True
                break
        if not related:
            fams.append(f0)
    return len(fams)

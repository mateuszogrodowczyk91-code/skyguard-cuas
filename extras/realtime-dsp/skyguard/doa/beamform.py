"""Kształtowanie wiązki i namiar z par mikrofonów.

- MVDR / Capon (metoda jak w spacialglaciercom-lab/drone-audio-pipeline —
  repozytorium bez licencji, kodu NIE kopiowano; własna implementacja),
- GCC-PHAT i SRP-PHAT (metoda jak w LCAV/pyroomacoustics, MIT — własna
  implementacja; pyroomacoustics nie jest wymagane).
Dla telefonu z 2 mikrofonami: `gcc_phat` → TDOA → `tdoa_to_bearing`."""
from __future__ import annotations

import numpy as np

from .ula import covariance, steering_vector

C_SOUND = 343.0


def mvdr_weights(R: np.ndarray, a: np.ndarray, diag_load: float = 1e-3) -> np.ndarray:
    M = R.shape[0]
    Rl = R + diag_load * np.trace(R).real / M * np.eye(M)
    Ri_a = np.linalg.solve(Rl, a)
    return Ri_a / (a.conj() @ Ri_a)


def mvdr_spectrum(X, grid=None, d_over_lambda: float = 0.5, diag_load: float = 1e-3):
    """P(θ) = 1 / (aᴴ R⁻¹ a) — wąskopasmowo, X: (M, snapshoty)."""
    grid = np.linspace(-90, 90, 1801) if grid is None else np.asarray(grid)
    R = covariance(X)
    M = R.shape[0]
    Rl = R + diag_load * np.trace(R).real / M * np.eye(M)
    Ri = np.linalg.inv(Rl)
    A = steering_vector(grid, M, d_over_lambda)
    return grid, 1.0 / np.real(np.sum(A.conj() * (Ri @ A), axis=0))


def gcc_phat(x, y, sr: int, max_tau: float | None = None, interp: int = 16):
    """Zwraca (tau [s], korelacja). tau > 0: `y` opóźnione względem `x`."""
    n = len(x) + len(y)
    X = np.fft.rfft(x, n)
    Y = np.fft.rfft(y, n)
    G = Y * np.conj(X)
    G /= np.abs(G) + 1e-15
    cc = np.fft.irfft(G, n * interp)
    max_shift = interp * n // 2
    if max_tau is not None:
        max_shift = min(int(interp * sr * max_tau), max_shift)
    cc = np.concatenate((cc[-max_shift:], cc[:max_shift + 1]))
    shift = np.argmax(np.abs(cc)) - max_shift
    return shift / float(interp * sr), cc


def tdoa_to_bearing(tau: float, mic_distance_m: float, c: float = C_SOUND) -> float:
    """Kąt od osi prostopadłej do pary mikrofonów [°]."""
    return float(np.degrees(np.arcsin(np.clip(tau * c / mic_distance_m, -1, 1))))


def srp_phat(signals: np.ndarray, mic_xy: np.ndarray, sr: int, az_grid=None, nfft: int = 1024,
             fmin: float = 100.0, fmax: float | None = None, c: float = C_SOUND):
    """SRP-PHAT w płaszczyźnie (pole dalekie). signals: (M, N), mic_xy: (M, 2) [m].
    Zwraca (azymuty[°], moc)."""
    az = np.arange(0, 360, 1.0) if az_grid is None else np.asarray(az_grid, float)
    M, N = signals.shape
    hop = nfft // 2
    k = 1 + (N - nfft) // hop
    win = np.hanning(nfft)
    frames = np.stack([np.fft.rfft(signals[:, i * hop:i * hop + nfft] * win, axis=1) for i in range(k)], 0)
    f = np.fft.rfftfreq(nfft, 1 / sr)
    sel = (f >= fmin) & (f <= (fmax or sr / 2))
    F = frames[:, :, sel]
    F = F / (np.abs(F) + 1e-15)
    u = np.stack([np.cos(np.radians(az)), np.sin(np.radians(az))], 1)  # (A,2)
    delays = (mic_xy @ u.T) / c  # (M,A): wcześniejsze przyjście dla mikrofonu bliżej źródła
    P = np.zeros(az.size)
    for a in range(az.size):
        steer = np.exp(-2j * np.pi * f[sel][None, :] * delays[:, a][:, None])  # (M,F)
        s = np.sum(F * steer[None], axis=1)
        P[a] = np.mean(np.abs(s) ** 2)
    return az, P

"""MUSIC (Schmidt 1986) i LS-ESPRIT (Roy & Kailath 1989) — własna implementacja."""
from __future__ import annotations

import numpy as np


def steering_vector(theta_deg, n_elem: int, d_over_lambda: float = 0.5) -> np.ndarray:
    th = np.deg2rad(np.atleast_1d(theta_deg))
    k = np.arange(n_elem)[:, None]
    return np.exp(-2j * np.pi * d_over_lambda * k * np.sin(th)[None, :])


def covariance(X) -> np.ndarray:
    """X: (n_elem, n_snapshots) -> macierz kowariancji próbkowej."""
    X = np.asarray(X)
    return X @ X.conj().T / X.shape[1]


def _noise_subspace(R, n_src):
    w, v = np.linalg.eigh(R)
    return v[:, : R.shape[0] - n_src]


def music_spectrum(X, n_src: int, grid=None, d_over_lambda: float = 0.5):
    grid = np.linspace(-90, 90, 1801) if grid is None else np.asarray(grid)
    R = covariance(X)
    En = _noise_subspace(R, n_src)
    A = steering_vector(grid, R.shape[0], d_over_lambda)
    denom = np.sum(np.abs(En.conj().T @ A) ** 2, axis=0)
    return grid, 1.0 / np.maximum(denom, 1e-15)


def music_doa(X, n_src: int, d_over_lambda: float = 0.5, grid=None) -> np.ndarray:
    g, p = music_spectrum(X, n_src, grid, d_over_lambda)
    pk = np.where((p[1:-1] > p[:-2]) & (p[1:-1] >= p[2:]))[0] + 1
    best = pk[np.argsort(p[pk])[::-1][:n_src]]
    return np.sort(g[best])


def esprit_doa(X, n_src: int, d_over_lambda: float = 0.5) -> np.ndarray:
    R = covariance(X)
    w, v = np.linalg.eigh(R)
    Es = v[:, -n_src:]
    E1, E2 = Es[:-1], Es[1:]
    psi = np.linalg.lstsq(E1, E2, rcond=None)[0]
    phases = np.angle(np.linalg.eigvals(psi))
    s = np.clip(-phases / (2 * np.pi * d_over_lambda), -1, 1)
    return np.sort(np.rad2deg(np.arcsin(s)))


def root_music_doa(X, n_src: int, d_over_lambda: float = 0.5) -> np.ndarray:
    """Root-MUSIC (metoda jak w morriswmz/doatools.py, MIT — własna implementacja):
    pierwiastki wielomianu z sum przekątnych E_n E_n^H najbliżej okręgu jednostkowego."""
    R = covariance(X)
    M = R.shape[0]
    En = _noise_subspace(R, n_src)
    C = En @ En.conj().T
    coeffs = np.array([np.trace(C, offset=k) for k in range(M - 1, -M, -1)])
    roots = np.roots(coeffs)
    roots = roots[np.abs(roots) < 1.0]
    roots = roots[np.argsort(np.abs(np.abs(roots) - 1.0))][:n_src]
    s = np.angle(roots) / (2 * np.pi * d_over_lambda)
    return np.sort(np.degrees(np.arcsin(np.clip(-s, -1, 1))))

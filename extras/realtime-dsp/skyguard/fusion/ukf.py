"""Bezzapachowy filtr Kalmana (UKF) — punkty sigma van der Merwe'a.

Źródło techniki: raport C-UAS (System 10, „UKF State Engine”). Raport przesadza,
że klasyczny KF jest „bezużyteczny”: dla pomiarów kartezjańskich KF jest optymalny.
UKF ma sens tam, gdzie pomiar jest nieliniowy (azymut/elewacja/odległość z mikrofonów
lub przyszłego radaru) — wtedy nie trzeba liczyć Jakobianu jak w EKF.
Implementacja własna wg Wan & van der Merwe (2000).
"""
from __future__ import annotations

from typing import Callable

import numpy as np


def merwe_sigma_points(x, P, alpha=1e-3, beta=2.0, kappa=0.0):
    n = x.size
    lam = alpha ** 2 * (n + kappa) - n
    S = np.linalg.cholesky((n + lam) * P)
    X = np.empty((2 * n + 1, n))
    X[0] = x
    for i in range(n):
        X[1 + i] = x + S[:, i]
        X[1 + n + i] = x - S[:, i]
    Wm = np.full(2 * n + 1, 1.0 / (2 * (n + lam)))
    Wc = Wm.copy()
    Wm[0] = lam / (n + lam)
    Wc[0] = lam / (n + lam) + (1 - alpha ** 2 + beta)
    return X, Wm, Wc


class UKF:
    """x' = f(x, dt), z = h(x). `residual_z` pozwala zawijać kąty (np. azymut ±180°)."""

    def __init__(self, x0, P0, f: Callable, h: Callable, Q, R,
                 alpha=0.1, beta=2.0, kappa=0.0, residual_z: Callable | None = None,
                 mean_z: Callable | None = None):
        self.x = np.asarray(x0, float)
        self.P = np.asarray(P0, float)
        self.f, self.h = f, h
        self.Q, self.R = np.asarray(Q, float), np.asarray(R, float)
        self.alpha, self.beta, self.kappa = alpha, beta, kappa
        self.residual_z = residual_z or (lambda a, b: a - b)
        self.mean_z = mean_z
        self._X = None

    def _sp(self):
        P = 0.5 * (self.P + self.P.T) + 1e-12 * np.eye(self.x.size)
        return merwe_sigma_points(self.x, P, self.alpha, self.beta, self.kappa)

    def predict(self, dt: float = 1.0):
        X, Wm, Wc = self._sp()
        Y = np.array([self.f(s, dt) for s in X])
        self.x = Wm @ Y
        d = Y - self.x
        self.P = (Wc[:, None] * d).T @ d + self.Q
        self._X, self._Wm, self._Wc = Y, Wm, Wc
        return self.x

    def update(self, z):
        z = np.asarray(z, float)
        X, Wm, Wc = self._sp()
        Z = np.array([np.atleast_1d(self.h(s)) for s in X])
        zm = self.mean_z(Z, Wm) if self.mean_z else Wm @ Z
        dz = np.array([self.residual_z(zi, zm) for zi in Z])
        dx = X - self.x
        S = (Wc[:, None] * dz).T @ dz + self.R
        C = (Wc[:, None] * dx).T @ dz
        K = C @ np.linalg.inv(S)
        y = self.residual_z(z, zm)
        self.x = self.x + K @ y
        self.P = self.P - K @ S @ K.T
        self.nis = float(y @ np.linalg.solve(S, y))  # znormalizowana innowacja (bramkowanie / test spójności)
        return self.x

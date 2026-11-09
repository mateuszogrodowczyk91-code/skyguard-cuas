"""Filtr cząsteczkowy (SIR) do śledzenia namiaru/pozycji przy niegaussowskich pomiarach.

Metody resamplingu zaadaptowane z rlabbe/filterpy (MIT, © 2015 Roger R. Labbe Jr.),
filterpy/monte_carlo/resampling.py: residual, stratified, systematic,
multinomial. Zmiany SKYGUARD: generator `np.random.Generator` zamiast
globalnego stanu, klasa `ParticleFilter` z efektywną liczbą cząstek (N_eff)."""
from __future__ import annotations

import numpy as np


def residual_resample(w, rng=None):
    rng = rng or np.random.default_rng()
    N = len(w)
    idx = np.zeros(N, int)
    num = np.floor(N * np.asarray(w)).astype(int)
    k = 0
    for i in range(N):
        for _ in range(num[i]):
            idx[k] = i
            k += 1
    res = N * np.asarray(w) - num
    if k < N:
        res /= res.sum()
        cs = np.cumsum(res)
        cs[-1] = 1.0
        idx[k:N] = np.searchsorted(cs, rng.random(N - k))
    return idx


def stratified_resample(w, rng=None):
    rng = rng or np.random.default_rng()
    N = len(w)
    pos = (rng.random(N) + np.arange(N)) / N
    cs = np.cumsum(w)
    cs[-1] = 1.0
    return np.searchsorted(cs, pos)


def systematic_resample(w, rng=None):
    rng = rng or np.random.default_rng()
    N = len(w)
    pos = (rng.random() + np.arange(N)) / N
    cs = np.cumsum(w)
    cs[-1] = 1.0
    return np.searchsorted(cs, pos)


def multinomial_resample(w, rng=None):
    rng = rng or np.random.default_rng()
    cs = np.cumsum(w)
    cs[-1] = 1.0
    return np.searchsorted(cs, rng.random(len(w)))


class ParticleFilter:
    """x_k = f(x_{k-1}) + szum; wagi ∝ likelihood(z | x)."""

    def __init__(self, particles: np.ndarray, transition, likelihood, resample=systematic_resample, seed=None):
        self.p = np.asarray(particles, float).copy()
        self.w = np.full(len(self.p), 1.0 / len(self.p))
        self.f, self.lik, self.resample = transition, likelihood, resample
        self.rng = np.random.default_rng(seed)

    def predict(self):
        self.p = self.f(self.p, self.rng)

    def update(self, z):
        self.w *= self.lik(z, self.p)
        self.w += 1e-300
        self.w /= self.w.sum()
        if self.neff() < len(self.w) / 2:
            idx = self.resample(self.w, self.rng)
            self.p, self.w = self.p[idx], np.full(len(idx), 1.0 / len(idx))

    def neff(self) -> float:
        return 1.0 / np.sum(self.w ** 2)

    def estimate(self):
        m = np.average(self.p, weights=self.w, axis=0)
        v = np.average((self.p - m) ** 2, weights=self.w, axis=0)
        return m, v

"""EKF (model stałej prędkości, pomiar dowolny h(x)) + algorytm węgierski + tracker."""
from __future__ import annotations

import numpy as np


class EKF:
    def __init__(self, x0, P0, F, Q, h, H_jac, R):
        self.x = np.asarray(x0, float)
        self.P = np.asarray(P0, float)
        self.F, self.Q, self.h, self.H_jac, self.R = F, Q, h, H_jac, np.asarray(R, float)

    def predict(self):
        F = self.F(self.x) if callable(self.F) else self.F
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        return self.x

    def innovation(self, z):
        H = self.H_jac(self.x)
        y = np.asarray(z, float) - self.h(self.x)
        S = H @ self.P @ H.T + self.R
        return y, S, H

    def update(self, z):
        y, S, H = self.innovation(z)
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I = np.eye(self.x.size)
        self.P = (I - K @ H) @ self.P @ (I - K @ H).T + K @ self.R @ K.T  # forma Josepha
        return self.x


def hungarian(cost) -> list[tuple[int, int]]:
    """Algorytm węgierski (Kuhn-Munkres, wersja O(n^3) z potencjałami).

    Działa dla macierzy prostokątnych; zwraca pary (wiersz, kolumna)."""
    C = np.asarray(cost, float)
    transposed = C.shape[0] > C.shape[1]
    if transposed:
        C = C.T
    n, m = C.shape
    INF = float("inf")
    u = np.zeros(n + 1); v = np.zeros(m + 1)
    p = np.zeros(m + 1, int); way = np.zeros(m + 1, int)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = np.full(m + 1, INF)
        used = np.zeros(m + 1, bool)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta, j1 = INF, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = C[i0 - 1, j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur; way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]; j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta; v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
            if j0 == 0:
                break
    pairs = [(p[j] - 1, j - 1) for j in range(1, m + 1) if p[j] != 0]
    if transposed:
        pairs = [(c, r) for r, c in pairs]
    return sorted(pairs)


class MultiTargetTracker:
    """Prosty tracker 2D (x, y, vx, vy) z pomiarami pozycji, bramka Mahalanobisa."""

    def __init__(self, dt=0.1, q=1.0, r=1.0, gate=9.21, max_miss=5):
        self.dt, self.q, self.r, self.gate, self.max_miss = dt, q, r, gate, max_miss
        self.tracks: list[dict] = []
        self._next = 1

    def _new_ekf(self, z):
        dt = self.dt
        F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], float)
        G = np.array([[dt**2 / 2, 0], [0, dt**2 / 2], [dt, 0], [0, dt]])
        Q = self.q * G @ G.T
        H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], float)
        return EKF([z[0], z[1], 0, 0], np.diag([self.r, self.r, 100, 100]), F, Q,
                   lambda x: H @ x, lambda x: H, np.eye(2) * self.r)

    def step(self, measurements):
        Z = [np.asarray(z, float) for z in measurements]
        for t in self.tracks:
            t["ekf"].predict()
        assigned_t, assigned_z = set(), set()
        if self.tracks and Z:
            cost = np.full((len(self.tracks), len(Z)), 1e6)
            for i, t in enumerate(self.tracks):
                for j, z in enumerate(Z):
                    y, S, _ = t["ekf"].innovation(z)
                    d2 = float(y @ np.linalg.solve(S, y))
                    if d2 < self.gate:
                        cost[i, j] = d2
            for i, j in hungarian(cost):
                if cost[i, j] < 1e6:
                    self.tracks[i]["ekf"].update(Z[j])
                    self.tracks[i]["miss"] = 0
                    self.tracks[i]["hits"] += 1
                    assigned_t.add(i); assigned_z.add(j)
        for i, t in enumerate(self.tracks):
            if i not in assigned_t:
                t["miss"] += 1
        self.tracks = [t for t in self.tracks if t["miss"] <= self.max_miss]
        for j, z in enumerate(Z):
            if j not in assigned_z:
                self.tracks.append({"id": self._next, "ekf": self._new_ekf(z), "miss": 0, "hits": 1})
                self._next += 1
        return [(t["id"], t["ekf"].x.copy()) for t in self.tracks]

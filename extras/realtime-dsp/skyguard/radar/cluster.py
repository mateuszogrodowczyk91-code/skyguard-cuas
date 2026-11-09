"""DBSCAN dla chmury punktów radaru (grupowanie detekcji CFAR w obiekty).

Metoda jak w 0xastro/fmcw-RADAR (MIT) — tam w C dla mikrokontrolera; tu
własna implementacja numpy/scipy (KD-drzewo), bez scikit-learn."""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def dbscan(points: np.ndarray, eps: float, min_samples: int = 3) -> np.ndarray:
    """Zwraca etykiety (−1 = szum)."""
    P = np.asarray(points, float)
    n = len(P)
    labels = np.full(n, -1)
    if n == 0:
        return labels
    nb = cKDTree(P).query_ball_point(P, eps)
    core = np.array([len(x) >= min_samples for x in nb])
    cid = 0
    for i in range(n):
        if labels[i] != -1 or not core[i]:
            continue
        labels[i] = cid
        stack = list(nb[i])
        while stack:
            j = stack.pop()
            if labels[j] == -1:
                labels[j] = cid
                if core[j]:
                    stack.extend(nb[j])
        cid += 1
    return labels


def cluster_centroids(points: np.ndarray, labels: np.ndarray) -> np.ndarray:
    ids = sorted(set(labels.tolist()) - {-1})
    return np.array([points[labels == k].mean(axis=0) for k in ids]).reshape(-1, points.shape[1] if len(points) else 0)

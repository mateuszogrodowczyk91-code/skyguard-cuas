"""Reguła kombinacji Dempstera. Masy jako dict[frozenset, float]."""
from __future__ import annotations

from itertools import product


def combine(m1: dict, m2: dict) -> dict:
    out: dict = {}
    conflict = 0.0
    for (a, x), (b, y) in product(m1.items(), m2.items()):
        c = frozenset(a) & frozenset(b)
        if c:
            out[c] = out.get(c, 0.0) + x * y
        else:
            conflict += x * y
    if conflict >= 1.0 - 1e-12:
        raise ValueError("całkowity konflikt źródeł (K=1)")
    return {k: v / (1.0 - conflict) for k, v in out.items()}


def belief(m: dict, h) -> float:
    h = frozenset(h)
    return sum(v for k, v in m.items() if frozenset(k) <= h)


def plausibility(m: dict, h) -> float:
    h = frozenset(h)
    return sum(v for k, v in m.items() if frozenset(k) & h)


# --- Zaadaptowane z reineking/pyds (BSD-3-Clause, © 2014 Thomas Reineking):
# reguła Yagera (konflikt trafia do niewiedzy Θ zamiast normalizacji — bezpieczna,
# gdy źródła się kłócą, np. akustyka „dron” vs RID „brak”) i transformacja
# pignistyczna BetP (decyzja z masy). Przepisane na nasze API dict[frozenset].

def combine_yager(m1: dict, m2: dict, frame=None) -> dict:
    frame = frozenset(frame) if frame is not None else frozenset().union(*m1.keys(), *m2.keys())
    out: dict = {}
    conflict = 0.0
    for (a, x), (b, y) in product(m1.items(), m2.items()):
        c = frozenset(a) & frozenset(b)
        if c:
            out[c] = out.get(c, 0.0) + x * y
        else:
            conflict += x * y
    out[frame] = out.get(frame, 0.0) + conflict
    return out


def pignistic(m: dict) -> dict:
    """BetP(x) = Σ_{A∋x} m(A)/|A|  (dla m(∅)=0)."""
    p: dict = {}
    for k, v in m.items():
        k = frozenset(k)
        if not k:
            continue
        for x in k:
            p[x] = p.get(x, 0.0) + v / len(k)
    return p

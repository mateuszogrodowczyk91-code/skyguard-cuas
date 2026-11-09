"""Uncertainty Wrapper (w stylu Fraunhofer IESE) dla decyzji detektora SG-FUZJA.

Źródło techniki: raport C-UAS (sekcja SPELL / „Uncertainty Wrapper”); koncepcja z
Kläs & Sembach, „Uncertainty Wrappers for Data-driven Models” (SAFECOMP 2019) i
Kläs & Jöckel (2020). Implementacja własna (bez kodu IESE, który nie jest otwarty).

Idea: model danych (tu: sieć SG-FUZJA) zwraca decyzję, a NIEZALEŻNY „wrapper” ocenia,
na ile tej decyzji można ufać w danej sytuacji. Trzy elementy:
  1. czynniki jakości (quality factors) — cechy sytuacji, nie samego celu:
     pewność sieci, głośność, stabilność i wyrazistość grzebienia harmonicznego,
     entropia widmowa, liczba rodzin wirników;
  2. model jakości — płytkie drzewo decyzyjne dzielące przestrzeń czynników na
     obszary o różnej częstości błędu; w każdym liściu niepewność = GÓRNA granica
     Cloppera–Pearsona (poziom ufności np. 95%) częstości błędu — konserwatywnie;
  3. model zgodności z zakresem (scope compliance) — jeśli czynniki są poza zakresem
     danych uczących, niepewność = 1 (nie wiemy, więc nie ufamy).

Zasada SKYGUARD: wrapper NIGDY nie kasuje alarmu — może go tylko przenieść z
„pewny” do „DO WERYFIKACJI”. Czerwony alarm nadal wymaga zgodności 3 sensorów
(fuzja); wrapper mówi, czy GŁOS AKUSTYKI w tej fuzji jest wiarygodny.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
from scipy.stats import beta as _beta

# Głośność (LUFS) celowo POMINIĘTA: w naszych danych ESC-50 jest znormalizowane (głośne),
# a nagrania dronów cichsze — drzewo uczyłoby się artefaktu zbioru, nie fizyki
# (z LUFS wychodzi 96,7% precyzji, ale to przeciek). Patrz docs/cuas-report-extraction.md.
DEFAULT_FACTORS = ("fz_max", "harmonic_score", "salience", "stability", "spectral_entropy",
                   "n_rotor_families")


def clopper_pearson_upper(k: int, n: int, conf: float = 0.95) -> float:
    """Jednostronna górna granica ufności dla proporcji k/n (dokładna, Clopper–Pearson)."""
    if n <= 0:
        return 1.0
    if k >= n:
        return 1.0
    return float(_beta.ppf(conf, k + 1, n - k))


def _gini(k, n):
    if n == 0:
        return 0.0
    p = k / n
    return 2 * p * (1 - p)


class UncertaintyWrapper:
    def __init__(self, factors=DEFAULT_FACTORS, max_depth: int = 3, min_leaf: int = 25,
                 conf: float = 0.95, scope_q: float = 0.005, scope_margin: float = 0.10):
        self.factors = tuple(factors)
        self.max_depth, self.min_leaf, self.conf = max_depth, min_leaf, conf
        self.scope_q, self.scope_margin = scope_q, scope_margin
        self.tree = None
        self.scope = None

    # ------------------------------------------------------------------ uczenie
    def _X(self, rows):
        if isinstance(rows, np.ndarray):
            return rows.astype(float)
        return np.array([[float(r[f]) for f in self.factors] for r in rows], float)

    def fit(self, rows, wrong) -> "UncertaintyWrapper":
        X = self._X(rows); y = np.asarray(wrong, bool)
        lo = np.quantile(X, self.scope_q, axis=0); hi = np.quantile(X, 1 - self.scope_q, axis=0)
        span = np.maximum(hi - lo, 1e-9)
        self.scope = dict(lo=(lo - self.scope_margin * span).tolist(), hi=(hi + self.scope_margin * span).tolist())
        self.tree = self._grow(X, y, 0)
        return self

    def _leaf(self, y):
        k, n = int(y.sum()), int(y.size)
        return dict(leaf=True, k=k, n=n, u=clopper_pearson_upper(k, n, self.conf))

    def _grow(self, X, y, depth):
        node = self._leaf(y)
        if depth >= self.max_depth or y.size < 2 * self.min_leaf or node["k"] in (0, node["n"]):
            return node
        best = None
        parent = _gini(y.sum(), y.size) * y.size
        for j in range(X.shape[1]):
            xs = X[:, j]
            for t in np.unique(np.quantile(xs, np.linspace(0.05, 0.95, 19))):
                L = xs <= t
                nl = int(L.sum()); nr = y.size - nl
                if nl < self.min_leaf or nr < self.min_leaf:
                    continue
                g = _gini(y[L].sum(), nl) * nl + _gini(y[~L].sum(), nr) * nr
                if best is None or g < best[0]:
                    best = (g, j, float(t), L)
        if best is None or best[0] >= parent - 1e-9:
            return node
        _, j, t, L = best
        return dict(leaf=False, j=j, factor=self.factors[j], t=t,
                    le=self._grow(X[L], y[L], depth + 1), gt=self._grow(X[~L], y[~L], depth + 1))

    # --------------------------------------------------------------- predykcja
    def in_scope(self, q) -> bool:
        q = np.asarray(q, float)
        return bool(np.all(q >= np.asarray(self.scope["lo"])) and np.all(q <= np.asarray(self.scope["hi"])))

    def uncertainty(self, row) -> float:
        q = self._X([row])[0] if not isinstance(row, np.ndarray) else row
        if not np.all(np.isfinite(q)) or not self.in_scope(q):
            return 1.0
        n = self.tree
        while not n["leaf"]:
            n = n["le"] if q[n["j"]] <= n["t"] else n["gt"]
        return float(n["u"])

    def gate(self, alarm: bool, row, u_max: float = 0.20) -> str:
        """Klasyfikacja wiarygodności decyzji akustyki:
        'PEWNA'          — alarm i niepewność ≤ u_max (głos akustyki liczy się w fuzji 3 sensorów),
        'DO_WERYFIKACJI' — alarm, ale niepewność > u_max (żółty, operator patrzy/słucha),
        'BRAK'           — brak alarmu (wrapper niczego nie dodaje ani nie kasuje)."""
        if not alarm:
            return "BRAK"
        return "PEWNA" if self.uncertainty(row) <= u_max else "DO_WERYFIKACJI"

    # ------------------------------------------------------------- zapis
    def to_dict(self):
        return dict(factors=list(self.factors), max_depth=self.max_depth, min_leaf=self.min_leaf,
                    conf=self.conf, scope=self.scope, tree=self.tree)

    @classmethod
    def from_dict(cls, d):
        w = cls(d["factors"], d["max_depth"], d["min_leaf"], d["conf"])
        w.scope, w.tree = d["scope"], d["tree"]
        return w

    def save(self, path):
        json.dump(self.to_dict(), open(path, "w"), indent=1)

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.load(open(path)))

    def describe_tree(self) -> str:
        out = []

        def rec(n, ind):
            if n["leaf"]:
                out.append(f"{ind}liść: błędy {n['k']}/{n['n']}, u95={n['u']:.3f}")
            else:
                out.append(f"{ind}{n['factor']} ≤ {n['t']:.3g}")
                rec(n["le"], ind + "  ")
                out.append(f"{ind}{n['factor']} > {n['t']:.3g}")
                rec(n["gt"], ind + "  ")
        rec(self.tree, "")
        return "\n".join(out)


@dataclass
class _Default:
    w: UncertaintyWrapper | None = None


_D = _Default()


def default_wrapper() -> UncertaintyWrapper:
    import os
    if _D.w is None:
        _D.w = UncertaintyWrapper.load(os.path.join(os.path.dirname(__file__), "data", "uw_sgfuzja.json"))
    return _D.w

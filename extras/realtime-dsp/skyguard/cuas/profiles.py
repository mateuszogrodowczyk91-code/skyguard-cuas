"""Profile sygnatur maszyn (BPF/RPM) i klasyfikacja KLASY WIELKOŚCI drona z f0.

Technika z raportu C-UAS (sekcja „Akustyka”, System 5 „BPF Extractor”):
    BPF = N_b · RPM / 60       (N_b — liczba łopat śmigła)
Raport nie podaje żadnych konkretnych modeli. Profile poniżej NIE są przepisane
z raportu — zostały WYUCZONE na naszych prawdziwych nagraniach:
  • neaptide (Tarot X6, Mavic 2 Enterprise, Matrice 300 RTK, Holybro S500),
  • Politechnika Świętokrzyska / Mięsikowska, CC-BY (Mavic Mini 2, Mavic 3,
    Phantom 4, Matrice 300, S900 — zawis 5–10 m).
Model fizyczny: przy podobnej prędkości końcówki łopaty BPF ∝ 1/D, więc
    log f0 = a + b·log D      (D — średnica śmigła w calach; b ≈ −1 dla stałej prędkości końcówki)
a, b dopasowane metodą najmniejszych kwadratów do median f0 poszczególnych maszyn
(tools/cuas-report/fit_profiles.py). Średnice śmigieł — dane producentów.

UWAGA: f0 z `skyguard.dsp.harmonic` to częstotliwość podstawowa grzebienia
harmonicznego — u większości maszyn = BPF, ale np. przy niewyważeniu bywa to
częstotliwość obrotowa wału (RPM/60). Klasa wielkości to WSKAZÓWKA dla operatora,
nie zmienia decyzji alarmowej SG-FUZJA.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, asdict

_DATA = os.path.join(os.path.dirname(__file__), "data", "profiles.json")


def bpf_hz(rpm: float, blades: int = 2) -> float:
    return blades * rpm / 60.0


def rpm_from_bpf(bpf: float, blades: int = 2) -> float:
    return 60.0 * bpf / blades


@dataclass(frozen=True)
class SizeClass:
    key: str
    label_pl: str
    d_min_in: float     # zakres średnicy śmigła [cale]
    d_max_in: float
    examples: tuple


SIZE_CLASSES = (
    SizeClass("micro", "mikro/mały (< 7″, zwykle < 250 g–0,6 kg; też FPV 5″)", 0.0, 7.0,
              ("DJI Mini 2", "FPV 5″")),
    SizeClass("consumer", "średni konsumencki/półprofesjonalny (7–12″, ~0,9–2 kg)", 7.0, 12.0,
              ("DJI Phantom 4", "DJI Mavic 3", "DJI Mavic 2 Enterprise", "Holybro S500")),
    SizeClass("large_multi", "duży wielowirnikowiec (12–19″, hexa/okto, 5–10 kg)", 12.0, 19.5,
              ("DJI S900", "Tarot X6")),
    SizeClass("heavy", "ciężki przemysłowy (≥ 19,5″, > 6 kg, udźwig)", 19.5, 99.0,
              ("DJI Matrice 300 RTK",)),
)


@dataclass(frozen=True)
class MachineProfile:
    """Zmierzony profil jednej maszyny (zawis/lot na naszych nagraniach)."""
    model: str
    prop_in: float
    blades: int
    f0_median_hz: float
    f0_p10_hz: float
    f0_p90_hz: float
    n_clips: int
    source: str

    @property
    def hover_rpm(self) -> float:
        return rpm_from_bpf(self.f0_median_hz, self.blades)


@dataclass
class SizeEstimate:
    f0_hz: float
    prop_in: float              # szacowana średnica śmigła
    prop_in_lo: float           # przedział ±1σ reszt modelu
    prop_in_hi: float
    size_class: str
    label_pl: str
    class_probs: dict
    nearest_models: list        # najbliższe zmierzone maszyny (model, odległość w oktawach)
    hover_rpm_if_2_blades: float

    def to_dict(self):
        return asdict(self)


class SignatureModel:
    def __init__(self, a: float, b: float, sigma_log: float, profiles: list[MachineProfile]):
        self.a, self.b, self.sigma_log = float(a), float(b), float(sigma_log)
        self.profiles = list(profiles)

    # --- zapis/odczyt ---
    @classmethod
    def load(cls, path: str = _DATA) -> "SignatureModel":
        d = json.load(open(path, encoding="utf-8"))
        return cls(d["a"], d["b"], d["sigma_log"], [MachineProfile(**p) for p in d["profiles"]])

    def save(self, path: str = _DATA, extra: dict | None = None):
        d = dict(a=self.a, b=self.b, sigma_log=self.sigma_log, profiles=[asdict(p) for p in self.profiles])
        if extra:
            d.update(extra)
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    @classmethod
    def fit(cls, profiles: list[MachineProfile]) -> "SignatureModel":
        import numpy as np
        X = np.log([p.prop_in for p in profiles]); y = np.log([p.f0_median_hz for p in profiles])
        w = np.sqrt([p.n_clips for p in profiles])
        A = np.c_[np.ones_like(X), X] * w[:, None]
        a, b = np.linalg.lstsq(A, y * w, rcond=None)[0]
        res = y - (a + b * X)
        sig = float(np.sqrt(np.average(res ** 2, weights=w ** 2) * len(X) / max(1, len(X) - 2)))
        return cls(a, b, max(sig, 0.05), profiles)

    # --- predykcja ---
    def prop_diameter(self, f0_hz: float) -> float:
        return math.exp((math.log(f0_hz) - self.a) / self.b)

    def estimate(self, f0_hz: float) -> SizeEstimate:
        from math import erf, sqrt, log
        lf = log(max(f0_hz, 1e-3))
        mu = (lf - self.a) / self.b            # log D
        sd = abs(self.sigma_log / self.b)      # niepewność log D
        cdf = lambda v: 0.5 * (1 + erf((v - mu) / (sd * sqrt(2))))
        probs = {}
        for c in SIZE_CLASSES:
            lo = -1e9 if c.d_min_in <= 0 else log(c.d_min_in)
            probs[c.key] = round(cdf(log(c.d_max_in)) - cdf(lo), 4)
        best = max(SIZE_CLASSES, key=lambda c: probs[c.key])
        near = sorted(((p.model, round(abs(math.log2(f0_hz / p.f0_median_hz)), 3)) for p in self.profiles),
                      key=lambda t: t[1])[:3]
        return SizeEstimate(f0_hz=float(f0_hz), prop_in=round(math.exp(mu), 2),
                            prop_in_lo=round(math.exp(mu - sd), 2), prop_in_hi=round(math.exp(mu + sd), 2),
                            size_class=best.key, label_pl=best.label_pl, class_probs=probs,
                            nearest_models=near, hover_rpm_if_2_blades=round(rpm_from_bpf(f0_hz, 2)))


def size_class_of_diameter(d_in: float) -> str:
    for c in SIZE_CLASSES:
        if c.d_min_in <= d_in < c.d_max_in:
            return c.key
    return SIZE_CLASSES[-1].key


_default = None


def default_model() -> SignatureModel:
    global _default
    if _default is None:
        _default = SignatureModel.load()
    return _default


def estimate_size(f0_hz: float) -> SizeEstimate:
    return default_model().estimate(f0_hz)

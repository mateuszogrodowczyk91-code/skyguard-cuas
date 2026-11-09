"""Fuzja torów z nieznaną korelacją: Covariance Intersection (CI) i Inverse CI (ICI).

Źródło techniki: raport C-UAS (sekcja „Covariance Intersection vs. Inverse Covariance
Intersection”, System 12). Wzory zweryfikowane z literaturą:
- CI: Julier & Uhlmann (1997):  P⁻¹ = ω P_A⁻¹ + (1-ω) P_B⁻¹,
  x = P (ω P_A⁻¹ x_A + (1-ω) P_B⁻¹ x_B),
- ICI: Noack, Sijs, Reinhardt, Hanebeck (2017):
  P⁻¹ = P_A⁻¹ + P_B⁻¹ − (ω P_A + (1-ω) P_B)⁻¹,
  x = P (K_A x_A + K_B x_B), gdzie
  K_A = P_A⁻¹ − ω Γ,  K_B = P_B⁻¹ − (1-ω) Γ,  Γ = (ω P_A + (1-ω) P_B)⁻¹.
ω wybieramy, minimalizując wyznacznik (lub ślad) wyniku — złoty podział na [0, 1].

Po co w SKYGUARD: telefon + PC (+ później kolejne węzły) śledzą TEN SAM cel niezależnie,
ale ich błędy są skorelowane (ten sam dźwięk, ta sama pogoda). Zwykłe uśrednianie
Kalmana zaniża niepewność i daje fałszywie „ostrą” pozycję; CI/ICI tego nie robią.
Kod własny (bez kopiowania).
"""
from __future__ import annotations

import numpy as np

_GR = (np.sqrt(5) - 1) / 2


def _golden(f, a=0.0, b=1.0, tol=1e-6, it=200):
    c, d = b - _GR * (b - a), a + _GR * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(it):
        if abs(b - a) < tol:
            break
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - _GR * (b - a); fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + _GR * (b - a); fd = f(d)
    return (a + b) / 2


def _crit(P, criterion):
    if criterion == "trace":
        return float(np.trace(P))
    s, ld = np.linalg.slogdet(P)
    return float(ld) if s > 0 else np.inf


def covariance_intersection(xa, Pa, xb, Pb, omega: float | None = None, criterion: str = "det"):
    """Zwraca (x, P, omega). Wynik jest spójny dla DOWOLNEJ korelacji krzyżowej."""
    xa, xb = np.asarray(xa, float), np.asarray(xb, float)
    Ia, Ib = np.linalg.inv(Pa), np.linalg.inv(Pb)

    def fuse(w):
        P = np.linalg.inv(w * Ia + (1 - w) * Ib)
        return P @ (w * Ia @ xa + (1 - w) * Ib @ xb), P

    if omega is None:
        omega = _golden(lambda w: _crit(fuse(w)[1], criterion))
    x, P = fuse(omega)
    return x, 0.5 * (P + P.T), float(omega)


def inverse_covariance_intersection(xa, Pa, xb, Pb, omega: float | None = None, criterion: str = "det"):
    """ICI (Noack i in. 2017): mniej zachowawcze niż CI, nadal spójne przy nieznanej
    wspólnej informacji. Zwraca (x, P, omega)."""
    xa, xb = np.asarray(xa, float), np.asarray(xb, float)
    Pa, Pb = np.asarray(Pa, float), np.asarray(Pb, float)
    Ia, Ib = np.linalg.inv(Pa), np.linalg.inv(Pb)

    def fuse(w):
        G = np.linalg.inv(w * Pa + (1 - w) * Pb)
        P = np.linalg.inv(Ia + Ib - G)
        Ka, Kb = Ia - w * G, Ib - (1 - w) * G
        return P @ (Ka @ xa + Kb @ xb), P

    if omega is None:
        omega = _golden(lambda w: _crit(fuse(w)[1], criterion))
    x, P = fuse(omega)
    return x, 0.5 * (P + P.T), float(omega)


def naive_kalman_fusion(xa, Pa, xb, Pb):
    """Fuzja zakładająca NIEZALEŻNOŚĆ (do porównań — przy korelacji jest niespójna)."""
    Ia, Ib = np.linalg.inv(Pa), np.linalg.inv(Pb)
    P = np.linalg.inv(Ia + Ib)
    return P @ (Ia @ np.asarray(xa, float) + Ib @ np.asarray(xb, float)), P

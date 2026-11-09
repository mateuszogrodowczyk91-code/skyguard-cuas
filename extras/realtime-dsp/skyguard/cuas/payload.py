"""Detektor możliwego ZRZUTU ŁADUNKU ze skoku częstotliwości BPF (ścieżka f0).

Źródło techniki: raport C-UAS (sekcja „Akustyka”, System 5 „BPF Extractor” i
System 21 „threat scoring … BPF payload”). Raport twierdzi, że przy zrzucie RPM
„rośnie ponad normę, a potem spada” — częściowo zgodne z literaturą: w arXiv
2602.09991 („Acoustic Drone Package Delivery Detection”) obserwowaną cechą jest
SPADEK BPF po uwolnieniu ładunku (mniejsza masa → mniejszy ciąg potrzebny do zawisu).
Krótki pik przed spadkiem może wynikać z reakcji regulatora, ale nie jest cechą pewną.

Algorytm (własny): wygładzenie medianą, potem dla każdego kandydata podziału ścieżki
porównanie MEDIAN przed/po w oknach ≥ min_seg_s; zdarzenie = trwała zmiana poziomu
≥ min_rel_step przy stabilnych odcinkach (MAD/mediana ≤ max_rel_mad). Wynik to
WSKAZÓWKA „możliwy zrzut” — manewr (np. przejście z zawisu w opadanie) też obniża BPF.

Fizyka progu: w zawisie ciąg ∝ RPM², więc po zrzucie ułamka masy m/M
    RPM_po / RPM_przed ≈ sqrt(1 − m/M)
Ścieżka f0 bywa na częstotliwości wału zamiast BPF (×1/2), więc stosunek przed/po
jest składany oktawowo do [0,6; 1,2) (wzrost RPM > 20% w zawisie = +44% ciągu — mało realny).
Próg 15% ≈ ładunek ≥ 28% masy startowej. Niższe progi (6%) dawały na naszych
prawdziwych zawisach w wietrze 18–25 km/h fałszywe „zrzuty” w 61% klipów
(BPF wędruje ±8–10% w ciągu sekund) — patrz tools/cuas-report/eval_payload.py.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from scipy.ndimage import median_filter

_LN2 = float(np.log(2.0))
_LO = float(np.log(0.6))


def _fold(step_log: float) -> float:
    """Składa stosunek do [0,6; 1,2): spadek do 40% (ładunek do 64% masy) albo wzrost do 20%."""
    return float((step_log - _LO) % _LN2 + _LO)


@dataclass
class PayloadEvent:
    t_s: float
    f_before_hz: float
    f_after_hz: float
    rel_change: float
    kind: str                  # "spadek_bpf" (możliwy zrzut) | "wzrost_bpf" (możliwe podjęcie/obciążenie)

    def to_dict(self):
        return asdict(self)


def detect_bpf_steps(track_hz, hop_s: float = 1024 / 8000, min_seg_s: float = 3.0, min_rel_step: float = 0.15,
                     max_rel_mad: float = 0.02, smooth: int = 5, max_transition_s: float = 0.8) -> list[PayloadEvent]:
    f = np.asarray(track_hz, float)
    f = f[np.isfinite(f) & (f > 0)] if f.size else f
    L = int(round(min_seg_s / hop_s))
    G = int(round(max_transition_s / hop_s))
    if f.size < 2 * L + G:
        return []
    fs = median_filter(f, size=smooth, mode="nearest")
    lf = np.log(fs)
    best = None
    for k in range(L, fs.size - L - G + 1):
        a, b = lf[k - L:k], lf[k + G:k + G + L]
        ma, mb = np.median(a), np.median(b)
        step = mb - ma
        step = _fold(step)   # składanie oktawowe: skok toru wał↔BPF (×2) to nie zrzut
        mad = max(np.median(np.abs(a - ma)), np.median(np.abs(b - mb)))
        if abs(step) >= np.log1p(min_rel_step) and mad <= max_rel_mad:
            score = abs(step) / (mad + 1e-3)
            if best is None or score > best[0]:
                best = (score, k, ma, mb)
    if best is None:
        return []
    _, k, ma, mb = best
    fb, fa = float(np.exp(ma)), float(np.exp(mb))
    rel = float(np.exp(_fold(mb - ma))) - 1
    return [PayloadEvent(t_s=round((k + G / 2) * hop_s, 3), f_before_hz=round(fb, 2), f_after_hz=round(fa, 2),
                         rel_change=round(rel, 4), kind="spadek_bpf" if rel < 0 else "wzrost_bpf")]

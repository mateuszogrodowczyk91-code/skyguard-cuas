"""Potok detektora akustycznego SKYGUARD (opis po alarmie + opcjonalne weto).

Zasada: wynik SG-FUZJA (sieć + fuzja w skyguard-centrum) NIE jest zmieniany.
Ten moduł dokłada „drugą opinię” z cech harmonicznych / entropii i opis
zdarzenia (f0, BPF, liczba wirników, głośność). Weto jest domyślnie
WYŁĄCZONE — włączyć je wolno tylko wtedy, gdy ewaluacja na naszych klipach
pokazała zero utraconych trafień drona (zob. docs/top25.md, sekcja „Ewaluacja”)."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from .dsp.entropy import spectral_entropy
from .dsp.harmonic import analyze_harmonics
from .dsp.loudness import integrated_loudness
from .dsp.spectral_gate import spectral_gate


@dataclass
class AcousticDescription:
    f0_hz: float
    salience: float
    stability: float
    n_rotor_families: int
    spectral_entropy: float
    loudness_lufs: float
    harmonic_score: float  # 0..1 — „na ile to brzmi jak wirnik”

    def to_dict(self):
        return asdict(self)


def describe(x, sr: int, denoise: bool = False) -> AcousticDescription:
    x = np.asarray(x, float)
    if denoise:
        x = spectral_gate(x, sr)
    h = analyze_harmonics(x, sr)
    se = spectral_entropy(x, sr, fmin=50, fmax=min(4000, sr / 2))
    L = integrated_loudness(x, sr)
    score = float(np.clip(h.salience / 3.0, 0, 1) * (0.5 + 0.5 * h.stability))
    return AcousticDescription(h.f0_hz, h.salience, h.stability, h.n_rotor_families, se, L, score)


@dataclass
class AcousticPipeline:
    """Łączy decyzję SG-FUZJA z drugą opinią. `veto_threshold=None` → weto wyłączone."""
    veto_threshold: float | None = None

    def decide(self, sgfuzja_alarm: bool, x, sr: int) -> tuple[bool, AcousticDescription | None]:
        if not sgfuzja_alarm:
            return False, None
        d = describe(x, sr)
        if self.veto_threshold is not None and d.harmonic_score < self.veto_threshold:
            return False, d
        return True, d

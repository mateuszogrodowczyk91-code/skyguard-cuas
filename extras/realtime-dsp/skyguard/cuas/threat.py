"""Ocena zagrożenia 1–5 i kolor alarmu.

Źródło techniki: raport C-UAS (System 21 „Threat Scoring”: CPA, prędkość opadania,
„BPF payload”, brak Remote ID). Wagi raportu nie są podane — poniżej reguły jawne,
audytowalne (każdy punkt ma uzasadnienie w `reasons`), a nie „czarna skrzynka”.

Rozdział odpowiedzialności (zasada SKYGUARD, nie zmieniana tutaj):
  • KOLOR alarmu = zgodność sensorów: 3 zgodne → CZERWONY (+ nagrywanie),
    2 → ŻÓŁTY „DO WERYFIKACJI”, 1 → brak alarmu (tylko log). Wrapper niepewności
    może obniżyć głos akustyki do „DO WERYFIKACJI”, nigdy nie podnosi koloru.
  • POZIOM ZAGROŻENIA 1–5 = jak groźny jest cel, gdy już jest wykryty.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def cpa(rel_pos_m, rel_vel_ms):
    """Najbliższe zbliżenie (CPA) do chronionego punktu: zwraca (d_cpa [m], t_cpa [s] ≥ 0)."""
    p = np.asarray(rel_pos_m, float); v = np.asarray(rel_vel_ms, float)
    vv = float(v @ v)
    t = 0.0 if vv < 1e-9 else max(0.0, -float(p @ v) / vv)
    return float(np.linalg.norm(p + v * t)), t


def alarm_colour(n_sensors_agree: int, acoustic_grade: str | None = None) -> str:
    """3 zgodne sensory → CZERWONY; 2 → ŻÓŁTY; inaczej BRAK. Akustyka 'DO_WERYFIKACJI'
    nie liczy się jako pełny głos: obniża liczbę zgodnych sensorów o 1."""
    n = int(n_sensors_agree)
    if acoustic_grade == "DO_WERYFIKACJI" and n > 0:
        n -= 1
    if n >= 3:
        return "CZERWONY"
    if n == 2:
        return "ZOLTY_DO_WERYFIKACJI"
    return "BRAK"


@dataclass
class ThreatInput:
    size_class: str | None = None              # z profiles.estimate_size
    remote_id_seen: bool = False               # nasze cele: brak RID (domyślnie False)
    rel_pos_m: tuple | None = None             # ENU względem chronionego punktu
    rel_vel_ms: tuple | None = None
    vz_ms: float | None = None                 # prędkość pionowa (+ w górę)
    payload_event: str | None = None           # "spadek_bpf" / "wzrost_bpf"
    protect_radius_m: float = 150.0
    horizon_s: float = 90.0
    n_rotor_families: int | None = None


@dataclass
class ThreatResult:
    level: int
    reasons: list = field(default_factory=list)
    d_cpa_m: float | None = None
    t_cpa_s: float | None = None


def score(t: ThreatInput) -> ThreatResult:
    lvl, why = 1, ["wykryty bezzałogowiec (poziom bazowy 1)"]
    d = tc = None
    if not t.remote_id_seen:
        lvl += 1; why.append("+1 brak Remote ID (niewspółpracujący)")
    if t.size_class in ("large_multi", "heavy"):
        lvl += 1; why.append(f"+1 duża klasa ({t.size_class}) — udźwig ładunku")
    if t.rel_pos_m is not None and t.rel_vel_ms is not None:
        d, tc = cpa(t.rel_pos_m, t.rel_vel_ms)
        if d <= t.protect_radius_m and tc <= t.horizon_s:
            lvl += 1; why.append(f"+1 kurs kolizyjny: CPA {d:.0f} m za {tc:.0f} s")
    elif t.rel_pos_m is not None and np.linalg.norm(t.rel_pos_m) <= t.protect_radius_m:
        lvl += 1; why.append("+1 cel w strefie chronionej")
    dive = t.vz_ms is not None and t.vz_ms <= -3.0
    if dive or t.payload_event == "spadek_bpf":
        lvl += 1
        why.append("+1 " + ("nurkowanie/opadanie ≥ 3 m/s" if dive else "skok BPF w dół — możliwy zrzut ładunku"))
    return ThreatResult(level=int(min(5, max(1, lvl))), reasons=why, d_cpa_m=d, t_cpa_s=tc)

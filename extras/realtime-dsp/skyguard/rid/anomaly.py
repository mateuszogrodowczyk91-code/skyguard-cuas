"""Kontrola wiarygodności Remote ID (wykrywanie podszywania / fałszywych nadajników).

Metoda wg iannil/open-remote-id-parser (MIT, src/analysis/anomaly_detector.cpp):
niemożliwa prędkość/wznoszenie z kolejnych pozycji („teleport”), powtórki tych samych
wiadomości (replay: ≥3 identyczne w 5 s), zmiana RSSI niezgodna ze zmianą pozycji
(model propagacji RSSI_ref −50 dBm @1 m, wykładnik 2.5, próg 20 dB, tolerancja 30%).
Od siebie (SKYGUARD): nierealna wysokość, zbyt duży zasięg odbioru, pilot zbyt
daleko od drona, nagły wysyp nowych ID.
Kod napisany od nowa w Pythonie; progi SKYGUARD zgodne z aplikacją Android
(prędkość > 60 m/s, wznoszenie > 50 m/s, wysokość > 2 km, odległość > 20 km,
pilot > 25 km, ≥ 5 nowych ID w 10 s)."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))


@dataclass
class Anomaly:
    uas_id: str
    kind: str
    detail: str


@dataclass
class RidAnomalyChecker:
    max_speed: float = 60.0
    max_climb: float = 50.0
    max_alt: float = 2000.0
    max_range_m: float = 20000.0
    max_pilot_m: float = 25000.0
    burst_n: int = 5
    burst_window_s: float = 10.0
    replay_window_s: float = 5.0
    replay_min_dup: int = 3
    min_rssi_change: float = 20.0
    rssi_tolerance: float = 0.3
    path_loss_exp: float = 2.5
    _last: dict = field(default_factory=dict)
    _hashes: dict = field(default_factory=dict)
    _rssi: dict = field(default_factory=dict)
    _first_seen: dict = field(default_factory=dict)

    def check(self, uas_id: str, t: float, lat: float, lon: float, alt: float | None = None,
              speed_h: float | None = None, own_pos: tuple | None = None, pilot_pos: tuple | None = None,
              raw: bytes | None = None, rssi: float | None = None) -> list[Anomaly]:
        out: list[Anomaly] = []
        if raw is not None:
            h = self._hashes.setdefault(uas_id, deque(maxlen=100))
            dup = sum(1 for (tt, hh) in h if hh == hash(raw) and t - tt < self.replay_window_s)
            if dup >= self.replay_min_dup:
                out.append(Anomaly(uas_id, "replay", f"{dup} identycznych wiadomości w {self.replay_window_s:.0f} s"))
            h.append((t, hash(raw)))
        if uas_id not in self._first_seen:
            self._first_seen[uas_id] = t
            recent = [k for k, v in self._first_seen.items() if t - v <= self.burst_window_s]
            if len(recent) >= self.burst_n:
                out.append(Anomaly(uas_id, "burst", f"{len(recent)} nowych ID w {self.burst_window_s:.0f} s"))
        if speed_h is not None and speed_h > self.max_speed:
            out.append(Anomaly(uas_id, "speed", f"deklarowana prędkość {speed_h:.0f} m/s"))
        if alt is not None and alt > self.max_alt:
            out.append(Anomaly(uas_id, "altitude", f"wysokość {alt:.0f} m"))
        if own_pos is not None:
            d = haversine_m(own_pos[0], own_pos[1], lat, lon)
            if d > self.max_range_m:
                out.append(Anomaly(uas_id, "range", f"odbiór z {d / 1000:.1f} km"))
        if pilot_pos is not None:
            d = haversine_m(pilot_pos[0], pilot_pos[1], lat, lon)
            if d > self.max_pilot_m:
                out.append(Anomaly(uas_id, "pilot_far", f"pilot {d / 1000:.1f} km od drona"))
        prev = self._last.get(uas_id)
        if prev is not None and t > prev[0]:
            dt = t - prev[0]
            v = haversine_m(prev[1], prev[2], lat, lon) / dt
            if v > self.max_speed:
                out.append(Anomaly(uas_id, "teleport", f"skok pozycji {v:.0f} m/s"))
            if alt is not None and prev[3] is not None and abs(alt - prev[3]) / dt > self.max_climb:
                out.append(Anomaly(uas_id, "climb", f"wznoszenie {abs(alt - prev[3]) / dt:.0f} m/s"))
        if rssi is not None:
            hist = self._rssi.setdefault(uas_id, deque(maxlen=100))
            if len(hist) >= 3 and prev is not None:
                diff = abs(rssi - sum(hist) / len(hist))
                if diff > self.min_rssi_change:
                    moved = haversine_m(prev[1], prev[2], lat, lon)
                    expected = 10 * self.path_loss_exp * math.log10(max(1.0, moved))
                    if diff > expected * (1 + self.rssi_tolerance):
                        out.append(Anomaly(uas_id, "rssi", f"zmiana RSSI {diff:.0f} dB przy ruchu {moved:.0f} m"))
            hist.append(rssi)
        self._last[uas_id] = (t, lat, lon, alt)
        return out

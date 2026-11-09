"""ASTERIX dla SKYGUARD: eksport torów jako CAT062 (binarnie + JSON dla Centrum) oraz
POPRAWNY dekoder I048/120 (prędkość dopplerowska) z CAT048.

Źródło techniki: raport C-UAS (sekcja „ASTERIX”, Systemy 6–7). Struktura pozycji
zweryfikowana ze specyfikacjami EUROCONTROL w formie maszynowej
(zoranbosnjak/asterix-specs, BSD-3: CAT062 ed. 1.21, CAT048 ed. 1.32).

CAT062 (SDPS Track Messages) — UAP (FRN): 1 I010, 2 spare, 3 I015, 4 I070, 5 I105,
6 I100, 7 I185, FX | 8 I210, 9 I060, 10 I245, 11 I380, 12 I040, 13 I080, 14 I290, FX |
15 I200, 16 I295, 17 I136, 18 I130, 19 I135, 20 I220, ...
Jednostki: I070 1/128 s od północy UTC; I105 180/2^25 °; I185 0,25 m/s (x=wschód, y=północ);
I130 6,25 ft; I220 6,25 ft/min.

Raport miesza dwie rzeczy: I062/100 to tor KARTEZJAŃSKI (x/y względem stacji),
a I062/105 to WGS-84 (lat/lon) — „WGS-84 Cartesian” w raporcie to pomyłka.
CAT129 to identyfikacja WSPÓŁPRACUJĄCYCH UAS (producent, numer seryjny, rejestracja) —
dla dronów bez Remote ID nie ma czym jej wypełnić, więc tory bezzałogowców bez
identyfikacji eksportujemy jako CAT062.

Błąd w kodzie Kotlin z raportu (CAT048): czyta I048/120 z bitu 0x40 drugiego oktetu
FSPEC (to FRN 9 = I240 Aircraft Identification), traktuje go jak 1 bajt ze znakiem
i pomija pozycje I070/I090/I130 — dekoder rozjeżdża się na pierwszym rekordzie.
Prawidłowo: I048/120 to FRN 20 (3. oktet FSPEC, bit 0x04), pozycja ZŁOŻONA
(oktet główny: CAL=0x80, RDS=0x40), CAL = 2 oktety: D (bit 16) + 10-bitowa wartość
w kodzie U2, 1 m/s. Implementacja: `decode_cat048`.
Kod własny.
"""
from __future__ import annotations

import math
import struct
from datetime import datetime, timezone

FT = 0.3048
_LSB_WGS = 180.0 / (1 << 25)


def _fspec(frns: set[int]) -> bytes:
    n = max(frns) if frns else 1
    octs = (n + 6) // 7
    out = bytearray(octs)
    for f in frns:
        o, b = (f - 1) // 7, (f - 1) % 7
        out[o] |= 0x80 >> b
    for i in range(octs - 1):
        out[i] |= 0x01
    return bytes(out)


def _read_fspec(b: bytes, i: int):
    frns, o = set(), 0
    while True:
        c = b[i]; i += 1
        for k in range(7):
            if c & (0x80 >> k):
                frns.add(o * 7 + k + 1)
        o += 1
        if not c & 1:
            return frns, i


def tod_128(t_unix: float) -> int:
    d = datetime.fromtimestamp(t_unix, timezone.utc)
    s = d.hour * 3600 + d.minute * 60 + d.second + d.microsecond / 1e6
    return int(round(s * 128)) % (86400 * 128)


def _s(v, lsb, bits):
    q = int(round(v / lsb))
    lim = 1 << (bits - 1)
    return max(-lim, min(lim - 1, q))


def encode_cat062_record(tr: dict, sac: int, sic: int, service_id: int = 1) -> bytes:
    """tr: dict(track_number, t (unix s), lat, lon, [alt_m], [vx_e, vy_n m/s], [vz m/s],
    [mono=True], [tentative], [alt_src: 0..7], [first], [last])."""
    items = {}
    items[1] = bytes([sac & 0xFF, sic & 0xFF])
    items[3] = bytes([service_id & 0xFF])
    items[4] = tod_128(tr["t"]).to_bytes(3, "big")
    items[5] = struct.pack(">ii", _s(tr["lat"], _LSB_WGS, 32), _s(tr["lon"], _LSB_WGS, 32))
    if tr.get("vx_e") is not None and tr.get("vy_n") is not None:
        items[7] = struct.pack(">hh", _s(tr["vx_e"], 0.25, 16), _s(tr["vy_n"], 0.25, 16))
    items[12] = struct.pack(">H", int(tr["track_number"]) & 0xFFFF)
    o1 = (0x80 if tr.get("mono", True) else 0) | ((tr.get("alt_src", 0) & 7) << 2) | \
         (0x02 if tr.get("tentative", False) else 0)
    o2 = (0x20 if tr.get("last") else 0) | (0x10 if tr.get("first") else 0)
    items[13] = bytes([o1 | 0x01, o2]) if o2 else bytes([o1])
    if tr.get("alt_m") is not None:
        items[18] = struct.pack(">h", _s(tr["alt_m"] / FT, 6.25, 16))
    if tr.get("vz") is not None:
        items[20] = struct.pack(">h", _s(tr["vz"] / FT * 60.0, 6.25, 16))
    return _fspec(set(items)) + b"".join(items[k] for k in sorted(items))


def encode_cat062(tracks: list[dict], sac: int = 0, sic: int = 1) -> bytes:
    recs = b"".join(encode_cat062_record(t, sac, sic) for t in tracks)
    return bytes([62]) + struct.pack(">H", 3 + len(recs)) + recs


def decode_cat062(block: bytes) -> list[dict]:
    """Dekoder pozycji, które sami emitujemy (do testów zwrotnych i dla Centrum)."""
    if block[0] != 62:
        raise ValueError("to nie CAT062")
    ln = struct.unpack(">H", block[1:3])[0]
    i, out = 3, []
    while i < ln:
        frns, i = _read_fspec(block, i)
        r = {}
        for f in sorted(frns):
            if f == 1:
                r["sac"], r["sic"] = block[i], block[i + 1]; i += 2
            elif f == 3:
                r["service_id"] = block[i]; i += 1
            elif f == 4:
                r["tod_s"] = int.from_bytes(block[i:i + 3], "big") / 128.0; i += 3
            elif f == 5:
                la, lo = struct.unpack(">ii", block[i:i + 8]); i += 8
                r["lat"], r["lon"] = la * _LSB_WGS, lo * _LSB_WGS
            elif f == 7:
                vx, vy = struct.unpack(">hh", block[i:i + 4]); i += 4
                r["vx_e"], r["vy_n"] = vx * 0.25, vy * 0.25
            elif f == 12:
                r["track_number"] = struct.unpack(">H", block[i:i + 2])[0]; i += 2
            elif f == 13:
                o = block[i]; i += 1
                r["mono"], r["alt_src"], r["tentative"] = bool(o & 0x80), (o >> 2) & 7, bool(o & 2)
                while o & 1:
                    o = block[i]; i += 1
            elif f == 18:
                r["alt_m"] = struct.unpack(">h", block[i:i + 2])[0] * 6.25 * FT; i += 2
            elif f == 20:
                r["vz"] = struct.unpack(">h", block[i:i + 2])[0] * 6.25 * FT / 60.0; i += 2
            else:
                raise ValueError(f"FRN {f} nieobsługiwany w tym dekoderze")
        out.append(r)
    return out


def cat062_json(tr: dict, sac: int = 0, sic: int = 1, extra: dict | None = None) -> dict:
    """Ten sam tor jako JSON z kluczami pozycji ASTERIX (dla Centrum / logów).
    `extra` → klucz "SP" (Special Purpose): klasa, BPF, zagrożenie, stan weryfikacji."""
    j = {"I062/010": {"SAC": sac, "SIC": sic}, "I062/015": 1,
         "I062/070": {"ToT_s": round(tod_128(tr["t"]) / 128.0, 4)},
         "I062/105": {"LAT": round(tr["lat"], 7), "LON": round(tr["lon"], 7)},
         "I062/040": int(tr["track_number"]) & 0xFFFF,
         "I062/080": {"MON": int(tr.get("mono", True)), "SRC": tr.get("alt_src", 0),
                      "CNF": int(tr.get("tentative", False))}}
    if tr.get("vx_e") is not None:
        j["I062/185"] = {"VX": round(tr["vx_e"], 2), "VY": round(tr["vy_n"], 2)}
    if tr.get("alt_m") is not None:
        j["I062/130"] = {"ALT_ft": round(tr["alt_m"] / FT, 1)}
    if tr.get("vz") is not None:
        j["I062/220"] = {"ROCD_ft_min": round(tr["vz"] / FT * 60.0, 1)}
    if extra:
        j["SP"] = extra
    return j


# ------------------------------------------------------------------ CAT048 (radar), poprawny dekoder
def _len_fixed(n):
    return lambda b, i: n


def _len_extended(b, i):
    j = i
    while b[j] & 1:
        j += 1
    return j - i + 1


def _len_repetitive(sz):
    return lambda b, i: 1 + b[i] * sz


def _len_compound(sizes):
    def f(b, i):
        j, prim = i, []
        while True:
            prim.append(b[j]); j += 1
            if not b[j - 1] & 1:
                break
        n = j - i
        k = 0
        for o, c in enumerate(prim):
            for bit in range(7):
                if c & (0x80 >> bit):
                    s = sizes[k] if k < len(sizes) else None
                    if s is None:
                        raise ValueError("nieznane podpole pozycji złożonej")
                    n += s(b, i + n) if callable(s) else s
                k += 1
        return n
    return f


# FRN → (pozycja, funkcja długości)  — CAT048 ed. 1.32
CAT048_ITEMS = {
    1: ("010", _len_fixed(2)), 2: ("140", _len_fixed(3)), 3: ("020", _len_extended), 4: ("040", _len_fixed(4)),
    5: ("070", _len_fixed(2)), 6: ("090", _len_fixed(2)), 7: ("130", _len_compound([1] * 7)),
    8: ("220", _len_fixed(3)), 9: ("240", _len_fixed(6)), 10: ("250", _len_repetitive(8)),
    11: ("161", _len_fixed(2)), 12: ("042", _len_fixed(4)), 13: ("200", _len_fixed(4)),
    14: ("170", _len_extended), 15: ("210", _len_fixed(4)), 16: ("030", _len_extended),
    17: ("080", _len_fixed(2)), 18: ("100", _len_fixed(4)), 19: ("110", _len_fixed(2)),
    20: ("120", _len_compound([2, lambda b, i: 1 + b[i] * 6])), 21: ("230", _len_fixed(2)),
    22: ("260", _len_fixed(7)), 23: ("055", _len_fixed(1)), 24: ("050", _len_fixed(2)),
    25: ("065", _len_fixed(1)), 26: ("060", _len_fixed(2)),
}


def _i120(raw: bytes) -> dict:
    prim, j, out = raw[0], 1, {}
    if prim & 0x80:
        v = (raw[j] << 8) | raw[j + 1]; j += 2
        cal = v & 0x3FF
        if cal & 0x200:
            cal -= 0x400
        out["doppler_doubtful"] = bool(v & 0x8000)
        out["doppler_cal_ms"] = cal
    if prim & 0x40:
        rep = raw[j]; j += 1
        out["raw"] = [dict(zip(("dop_ms", "amb_ms", "frq_mhz"), struct.unpack(">HHH", raw[j + 6 * k:j + 6 * k + 6])))
                      for k in range(rep)]
    return out


def decode_cat048(block: bytes) -> list[dict]:
    if block[0] != 48:
        raise ValueError("to nie CAT048")
    ln = struct.unpack(">H", block[1:3])[0]
    i, out = 3, []
    while i < ln:
        frns, i = _read_fspec(block, i)
        r = {}
        for f in sorted(frns):
            if f not in CAT048_ITEMS:
                raise ValueError(f"FRN {f} (SP/RE) nieobsługiwany")
            name, lf = CAT048_ITEMS[f]
            n = lf(block, i)
            raw = block[i:i + n]; i += n
            if name == "010":
                r["sac"], r["sic"] = raw[0], raw[1]
            elif name == "140":
                r["tod_s"] = int.from_bytes(raw, "big") / 128.0
            elif name == "040":
                rho, th = struct.unpack(">HH", raw)
                r["rho_nm"], r["theta_deg"] = rho / 256.0, th * 360.0 / 65536
            elif name == "161":
                r["track_number"] = struct.unpack(">H", raw)[0] & 0x0FFF
            elif name == "120":
                r.update(_i120(raw))
            else:
                r["I048/" + name] = raw.hex()
        out.append(r)
    return out


def encode_cat048_test_record(sac, sic, tod_s, rho_nm, theta_deg, doppler_ms, with_i070_i090_i130=True) -> bytes:
    """Generator rekordów testowych (pozycje 010,140,020,040,[070,090,130],161,120)."""
    it = {1: bytes([sac, sic]), 2: int(tod_s * 128).to_bytes(3, "big"), 3: bytes([0x20]),
          4: struct.pack(">HH", int(rho_nm * 256), int(theta_deg / 360 * 65536) & 0xFFFF)}
    if with_i070_i090_i130:
        it[5] = b"\x0f\xff"; it[6] = b"\x05\xdc"; it[7] = bytes([0x82, 0x12, 0x34])  # 130: SRL + APD? → 2 podpola
    it[11] = struct.pack(">H", 123)
    v = doppler_ms & 0x3FF
    it[20] = bytes([0x80]) + struct.pack(">H", v)
    body = _fspec(set(it)) + b"".join(it[k] for k in sorted(it))
    return bytes([48]) + struct.pack(">H", 3 + len(body)) + body


def enu_from_bearing(az_deg: float, speed_ms: float) -> tuple[float, float]:
    a = math.radians(az_deg)
    return speed_ms * math.sin(a), speed_ms * math.cos(a)

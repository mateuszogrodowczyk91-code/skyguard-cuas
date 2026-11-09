"""SAPIENT (BSI Flex 335 v2.0) — węzeł czujnikowy (ASM) SKYGUARD.

Źródło techniki: raport C-UAS (sekcja „SAPIENT”, System 8 „SAPIENT Bus Router”,
4 warstwy zgodności). Szczegóły protokołu zweryfikowane ze schematem:
  dstl/SAPIENT-Proto-Files, katalog bsi_flex_335_v2_0 (© Crown Copyright, Apache-2.0).
Numery pól i wartości enumów poniżej pochodzą z tego schematu (atrybucja w
THIRD_PARTY_LICENSES.md); koder protobuf jest napisany od zera i nie wymaga
pakietu `protobuf` — zgodność bajt-w-bajt sprawdza tools/cuas-report/verify_sapient_protoc.py.

Ramka TCP (ICD §4.2): 4-bajtowy prefiks długości, uint32 LITTLE-ENDIAN, liczący
tylko ładunek, potem zserializowany SapientMessage.

Warstwy zgodności (raport): składniowa (prefiks + poprawny protobuf), strukturalna
(pola obowiązkowe), semantyczna (zakresy wartości, ULID, UUID), stanowa (najpierw
Registration → RegistrationAck(acceptance=true), dopiero potem DetectionReport).
Wszystkie cztery są tu egzekwowane po stronie nadawcy.
"""
from __future__ import annotations

import os
import struct
import time
import uuid

ICD_VERSION = "BSI Flex 335 v2.0"

# ---------------------------------------------------------------- ULID (Crockford base32)
_CROCK = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid(ts_ms: int | None = None) -> str:
    ts = int(time.time() * 1000) if ts_ms is None else int(ts_ms)
    v = (ts & ((1 << 48) - 1)) << 80 | int.from_bytes(os.urandom(10), "big")
    return "".join(_CROCK[(v >> (5 * i)) & 31] for i in range(25, -1, -1))


def is_ulid(s: str) -> bool:
    return isinstance(s, str) and len(s) == 26 and s[0] in "01234567" and all(c in _CROCK for c in s)


# ---------------------------------------------------------------- minimalny koder protobuf
# typy: s=string, d=double, f=float, b=bool, i=int32/enum (varint), q=int64 (varint), m=wiadomość
# schemat: {pole: (numer, typ, podschemat_lub_None, powtarzalne)}
# google.protobuf.Timestamp ma pola BEZ jawnej obecności (proto3 implicit) → zera się pomija;
# pola SAPIENT są `optional` (jawna obecność) → zera się zapisuje.
TS = {"seconds": (1, "q", None, False), "nanos": (2, "i", None, False), "__implicit__": True}
RANGE_BEARING = {"elevation": (1, "d", None, False), "azimuth": (2, "d", None, False), "range": (3, "d", None, False),
                 "elevation_error": (4, "d", None, False), "azimuth_error": (5, "d", None, False),
                 "range_error": (6, "d", None, False), "coordinate_system": (7, "i", None, False),
                 "datum": (8, "i", None, False)}
LOCATION = {"x": (1, "d", None, False), "y": (2, "d", None, False), "z": (3, "d", None, False),
            "x_error": (4, "d", None, False), "y_error": (5, "d", None, False), "z_error": (6, "d", None, False),
            "coordinate_system": (7, "i", None, False), "datum": (8, "i", None, False),
            "utm_zone": (9, "s", None, False)}
SUBCLASS: dict = {"type": (1, "s", None, False), "confidence": (2, "f", None, False), "level": (3, "i", None, False)}
SUBCLASS["sub_class"] = (4, "m", SUBCLASS, True)
CLASSIFICATION = {"type": (1, "s", None, False), "confidence": (2, "f", None, False),
                  "sub_class": (3, "m", SUBCLASS, True)}
BEHAVIOUR = {"type": (1, "s", None, False), "confidence": (2, "f", None, False)}
OBJECT_INFO = {"type": (1, "s", None, False), "value": (2, "s", None, False), "error": (3, "f", None, False)}
SIGNAL = {"amplitude": (1, "f", None, False), "start_frequency": (2, "f", None, False),
          "centre_frequency": (3, "f", None, False), "stop_frequency": (4, "f", None, False),
          "pulse_duration": (5, "f", None, False)}
DETECTION_REPORT = {"report_id": (1, "s", None, False), "object_id": (2, "s", None, False),
                    "task_id": (3, "s", None, False), "state": (4, "s", None, False),
                    "range_bearing": (5, "m", RANGE_BEARING, False), "location": (6, "m", LOCATION, False),
                    "detection_confidence": (7, "f", None, False), "track_info": (8, "m", OBJECT_INFO, True),
                    "object_info": (10, "m", OBJECT_INFO, True), "classification": (11, "m", CLASSIFICATION, True),
                    "behaviour": (12, "m", BEHAVIOUR, True), "signal": (14, "m", SIGNAL, True),
                    "colour": (22, "s", None, False), "id": (23, "s", None, False)}
DURATION = {"units": (1, "i", None, False), "value": (3, "f", None, False)}
REGION_DEF = {"region_type": (1, "i", None, True), "settle_time": (2, "m", DURATION, False)}
TASK_DEF = {"concurrent_tasks": (1, "i", None, False), "region_definition": (2, "m", REGION_DEF, False)}
MODE_DEF = {"mode_name": (1, "s", None, False), "mode_type": (2, "i", None, False),
            "mode_description": (3, "s", None, False), "settle_time": (4, "m", DURATION, False),
            "maximum_latency": (5, "m", DURATION, False), "scan_type": (6, "i", None, False),
            "tracking_type": (7, "i", None, False), "task": (11, "m", TASK_DEF, False)}
CONFIG = {"manufacturer": (1, "s", None, False), "model": (2, "s", None, False), "serial_number": (3, "s", None, False),
          "hardware_version": (4, "s", None, False), "software_version": (5, "s", None, False)}
REGISTRATION = {"node_definition": (1, "m", {"node_type": (1, "i", None, False),
                                             "node_sub_type": (2, "s", None, True)}, True),
                "icd_version": (2, "s", None, False), "name": (3, "s", None, False),
                "short_name": (4, "s", None, False),
                "capabilities": (5, "m", {"category": (1, "s", None, False), "type": (2, "s", None, False),
                                          "value": (3, "s", None, False), "units": (4, "s", None, False)}, True),
                "status_definition": (6, "m", {"status_interval": (1, "m", DURATION, False)}, False),
                "mode_definition": (7, "m", MODE_DEF, True), "config_data": (10, "m", CONFIG, True)}
REGISTRATION_ACK = {"acceptance": (1, "b", None, False), "ack_response_reason": (3, "s", None, True)}
SAPIENT_MESSAGE = {"timestamp": (1, "m", TS, False), "node_id": (2, "s", None, False),
                   "destination_id": (3, "s", None, False), "registration": (4, "m", REGISTRATION, False),
                   "registration_ack": (5, "m", REGISTRATION_ACK, False),
                   "detection_report": (7, "m", DETECTION_REPORT, False),
                   "additional_information": (13, "s", None, False)}


def _varint(v: int) -> bytes:
    if v < 0:
        v &= (1 << 64) - 1
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def encode(msg: dict, schema: dict) -> bytes:
    """Serializacja proto3 (pola w kolejności numerów, jak w oficjalnych bibliotekach)."""
    out = bytearray()
    implicit = schema.get("__implicit__", False)
    for name, (num, typ, sub, rep) in sorted(((k, v) for k, v in schema.items() if k != "__implicit__"),
                                             key=lambda kv: kv[1][0]):
        if name not in msg or msg[name] is None or (implicit and not rep and msg[name] in (0, 0.0, "", False)):
            continue
        vals = msg[name] if rep else [msg[name]]
        if rep and typ in "difbq":  # packed (domyślne w proto3 dla skalarów)
            body = b"".join(_scalar(typ, v) for v in vals)
            out += _varint(num << 3 | 2) + _varint(len(body)) + body
            continue
        for v in vals:
            if typ == "m":
                b = encode(v, sub)
                out += _varint(num << 3 | 2) + _varint(len(b)) + b
            elif typ == "s":
                b = v.encode("utf-8")
                out += _varint(num << 3 | 2) + _varint(len(b)) + b
            elif typ == "d":
                out += _varint(num << 3 | 1) + struct.pack("<d", v)
            elif typ == "f":
                out += _varint(num << 3 | 5) + struct.pack("<f", v)
            else:
                out += _varint(num << 3 | 0) + _scalar(typ, v)
    return bytes(out)


def _scalar(typ, v):
    if typ == "d":
        return struct.pack("<d", v)
    if typ == "f":
        return struct.pack("<f", v)
    return _varint(int(bool(v)) if typ == "b" else int(v))


def _read_varint(b, i):
    r = s = 0
    while True:
        if i >= len(b):
            raise SapientProtocolError("ucięty varint")
        c = b[i]; i += 1
        r |= (c & 0x7F) << s; s += 7
        if not c & 0x80:
            return r, i


def decode(b: bytes, schema: dict) -> dict:
    """Dekoder dla pól ze schematu (nieznane pola są pomijane, jak w protobuf)."""
    by_num = {v[0]: (k, *v[1:]) for k, v in schema.items() if k != "__implicit__"}
    out: dict = {}
    i = 0
    while i < len(b):
        key, i = _read_varint(b, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            raw, i = _read_varint(b, i)
        elif wt == 1:
            raw = b[i:i + 8]; i += 8
        elif wt == 5:
            raw = b[i:i + 4]; i += 4
        elif wt == 2:
            ln, i = _read_varint(b, i)
            raw = b[i:i + ln]; i += ln
        else:
            raise SapientProtocolError(f"nieobsługiwany typ drutu {wt}")
        if i > len(b):
            raise SapientProtocolError("ucięta wiadomość")
        if num not in by_num:
            continue
        name, typ, sub, rep = by_num[num]
        if typ == "m":
            v = decode(raw, sub)
        elif typ == "s":
            v = raw.decode("utf-8")
        elif typ == "d":
            v = struct.unpack("<d", raw)[0]
        elif typ == "f":
            v = struct.unpack("<f", raw)[0]
        elif typ == "b":
            v = bool(raw)
        else:
            if wt == 2:  # packed
                vals, j = [], 0
                while j < len(raw):
                    x, j = _read_varint(raw, j); vals.append(x)
                out.setdefault(name, []).extend(vals)
                continue
            v = raw if raw < (1 << 63) else raw - (1 << 64)
        if rep:
            out.setdefault(name, []).append(v)
        else:
            out[name] = v
    return out


# ---------------------------------------------------------------- ramkowanie TCP
def frame(payload: bytes) -> bytes:
    return struct.pack("<I", len(payload)) + payload


class FrameAccumulator:
    """Składa strumień TCP w ramki (prefiks LE uint32). Ochrona przed gigantycznymi długościami."""

    def __init__(self, max_len: int = 1 << 22):
        self.buf = bytearray(); self.max_len = max_len

    def feed(self, data: bytes) -> list[bytes]:
        self.buf += data
        out = []
        while len(self.buf) >= 4:
            (n,) = struct.unpack_from("<I", self.buf, 0)
            if n > self.max_len:
                raise SapientProtocolError(f"ramka {n} B > limit {self.max_len} B")
            if len(self.buf) < 4 + n:
                break
            out.append(bytes(self.buf[4:4 + n])); del self.buf[:4 + n]
        return out


# ---------------------------------------------------------------- sesja węzła
class SapientProtocolError(ValueError):
    pass


class SapientSequenceError(SapientProtocolError):
    pass


NODE_TYPE_ACOUSTIC, NODE_TYPE_PASSIVE_RF, NODE_TYPE_FUSION = 6, 8, 20
RB_DEGREES_M, RB_DATUM_TRUE, RB_DATUM_MAGNETIC = 1, 1, 2
LOC_LATLNG_DEG_M, LOC_DATUM_WGS84_E = 1, 1


def _ts(t=None):
    t = time.time() if t is None else t
    s = int(t)
    return {"seconds": s, "nanos": int(round((t - s) * 1e9)) % 1_000_000_000}


class SapientNode:
    """Stan: UNREGISTERED → AWAITING_ACK → REGISTERED (lub REJECTED)."""

    def __init__(self, name="SKYGUARD akustyka", node_id: str | None = None,
                 node_type: int = NODE_TYPE_ACOUSTIC, software_version: str = "skyguard"):
        self.node_id = node_id or str(uuid.uuid4())
        uuid.UUID(self.node_id)  # walidacja semantyczna
        self.name, self.node_type, self.sw = name, node_type, software_version
        self.state = "UNREGISTERED"
        self.reject_reasons: list[str] = []

    def _wrap(self, key, body, t=None, destination_id=None):
        m = {"timestamp": _ts(t), "node_id": self.node_id, key: body}
        if destination_id:
            m["destination_id"] = destination_id
        return m

    def registration(self, t=None) -> dict:
        reg = {
            "node_definition": [{"node_type": self.node_type, "node_sub_type": ["drone acoustic detector"]}],
            "icd_version": ICD_VERSION, "name": self.name, "short_name": "SKYGUARD",
            "capabilities": [{"category": "Acoustic", "type": "Frequency range", "value": "60-4000", "units": "Hz"},
                             {"category": "Acoustic", "type": "Remote ID required", "value": "false"}],
            "status_definition": {"status_interval": {"units": 4, "value": 5.0}},
            "mode_definition": [{"mode_name": "default", "mode_type": 3, "settle_time": {"units": 4, "value": 1.0},
                                 "scan_type": 1, "tracking_type": 2,
                                 "task": {"concurrent_tasks": 1,
                                          "region_definition": {"region_type": [1],
                                                                "settle_time": {"units": 4, "value": 1.0}}}}],
            "config_data": [{"manufacturer": "SKYGUARD", "model": "SG-FUZJA", "software_version": self.sw}],
        }
        self.state = "AWAITING_ACK"
        return self._wrap("registration", reg, t)

    def handle(self, msg: dict):
        if "registration_ack" in msg:
            if self.state != "AWAITING_ACK":
                raise SapientSequenceError("RegistrationAck bez wysłanej rejestracji")
            ack = msg["registration_ack"]
            if ack.get("acceptance"):
                self.state = "REGISTERED"
            else:
                self.state = "REJECTED"; self.reject_reasons = list(ack.get("ack_response_reason", []))
        return self.state

    def detection_report(self, *, object_id: str, confidence: float, azimuth_deg: float | None = None,
                         azimuth_err_deg: float | None = None, range_m: float | None = None,
                         elevation_deg: float | None = None, lat: float | None = None, lon: float | None = None,
                         alt_m: float | None = None, classification: list | None = None,
                         behaviour: list | None = None, object_info: list | None = None,
                         signal: list | None = None, state: str | None = None, t=None,
                         report_id: str | None = None) -> dict:
        if self.state != "REGISTERED":
            raise SapientSequenceError(f"DetectionReport w stanie {self.state} — najpierw Registration/Ack")
        if not is_ulid(object_id):
            raise SapientProtocolError("object_id musi być ULID")
        if not 0.0 <= confidence <= 1.0:
            raise SapientProtocolError("detection_confidence poza [0,1]")
        dr = {"report_id": report_id or new_ulid(), "object_id": object_id, "detection_confidence": float(confidence)}
        if state:
            dr["state"] = state
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise SapientProtocolError("współrzędne poza zakresem")
            dr["location"] = {"x": float(lon), "y": float(lat), "coordinate_system": LOC_LATLNG_DEG_M,
                              "datum": LOC_DATUM_WGS84_E, **({"z": float(alt_m)} if alt_m is not None else {})}
        elif azimuth_deg is not None:
            rb = {"azimuth": float(azimuth_deg) % 360.0, "coordinate_system": RB_DEGREES_M, "datum": RB_DATUM_TRUE}
            if azimuth_err_deg is not None:
                rb["azimuth_error"] = float(azimuth_err_deg)
            if elevation_deg is not None:
                rb["elevation"] = float(elevation_deg)
            if range_m is not None:
                rb["range"] = float(range_m)
            dr["range_bearing"] = rb
        else:
            raise SapientProtocolError("DetectionReport wymaga location albo range_bearing (oneof obowiązkowy)")
        for k, v in (("classification", classification), ("behaviour", behaviour),
                     ("object_info", object_info), ("signal", signal)):
            if v:
                dr[k] = v
        return self._wrap("detection_report", dr, t)


def validate_structure(msg: dict) -> list[str]:
    """Warstwa strukturalna: brakujące pola obowiązkowe (lista błędów, pusta = OK)."""
    err = []
    for k in ("timestamp", "node_id"):
        if k not in msg:
            err.append(f"brak {k}")
    if "detection_report" in msg:
        d = msg["detection_report"]
        for k in ("report_id", "object_id"):
            if k not in d:
                err.append(f"detection_report.{k}")
        if "range_bearing" not in d and "location" not in d:
            err.append("detection_report: brak location/range_bearing")
        rb = d.get("range_bearing")
        if rb is not None and ("coordinate_system" not in rb or "datum" not in rb):
            err.append("range_bearing: coordinate_system/datum obowiązkowe")
    if "registration" in msg:
        r = msg["registration"]
        for k in ("node_definition", "icd_version", "capabilities", "status_definition", "mode_definition",
                  "config_data"):
            if not r.get(k):
                err.append(f"registration.{k}")
    return err


def to_wire(msg: dict) -> bytes:
    e = validate_structure(msg)
    if e:
        raise SapientProtocolError("; ".join(e))
    return frame(encode(msg, SAPIENT_MESSAGE))


def from_payload(payload: bytes) -> dict:
    return decode(payload, SAPIENT_MESSAGE)

"""DJI DroneID w ramkach Wi-Fi beacon (element dostawcy OUI 26:37:12).

Port naszego dekodera z aplikacji Android
(app/src/main/java/com/skyguard/radar/data/DjiWifiDroneIdDecoder.kt).
Metoda opisana publicznie m.in. w ByteMe1001/DJI-DroneID-Scanner (bez
licencji — kodu nie kopiowano) i w formacie Kismet (GPL — kodu nie
kopiowano); tu tylko własna implementacja układu pól."""
from __future__ import annotations

import math
import struct

DJI_OUI = bytes([0x26, 0x37, 0x12])
SUB_FLIGHT, SUB_PURPOSE = 0x10, 0x11
COORD_DIV = 174533.0
PRODUCTS = {1: "Inspire 1", 2: "Phantom 3", 11: "Phantom 4", 16: "Mavic Pro", 21: "Spark", 24: "Mavic Air",
            41: "Mavic 2", 53: "Mavic Mini", 58: "Mavic Air 2", 60: "M300 RTK", 61: "DJI FPV", 63: "Mini 2",
            66: "Air 2S", 67: "M30", 68: "Mavic 3", 70: "Mini SE"}


def _s16(b, i):
    return struct.unpack_from("<h", b, i)[0]


def _s32(b, i):
    return struct.unpack_from("<i", b, i)[0]


def _ascii(b, a, z):
    s = bytes(b[a:z]).split(b"\x00", 1)[0]
    s = "".join(chr(c) for c in s if 0x20 <= c <= 0x7E).strip()
    return s or None


def _coord(raw_lat, raw_lon):
    if raw_lat == 0 and raw_lon == 0:
        return None
    lat, lon = raw_lat / COORD_DIV, raw_lon / COORD_DIV
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (abs(lat) < 0.01 and abs(lon) < 0.01):
        return None
    return lat, lon


def parse_dji_vendor_ie(body: bytes) -> dict | None:
    """`body` zaczyna się od OUI. Zwraca dict lub None."""
    if body is None or len(body) < 8 or body[:3] != DJI_OUI or body[6] not in (SUB_FLIGHT, SUB_PURPOSE):
        return None
    b = bytes(body)
    if b[6] == SUB_PURPOSE:
        if len(b) < 24:
            return None
        return {"kind": "purpose", "serial": _ascii(b, 8, 24), "drone_id": _ascii(b, 25, 35),
                "purpose": _ascii(b, 36, len(b))}
    if len(b) < 36:
        return None
    ver = b[7]
    out = {"kind": "flight", "version": ver, "serial": _ascii(b, 12, 28), "position": _coord(_s32(b, 32), _s32(b, 28))}
    vn = ve = vu = 0
    if ver >= 2:
        if len(b) >= 48:
            out.update(alt_m=_s16(b, 36) / 10, height_m=_s16(b, 38) / 10, yaw_deg=_s16(b, 46) / 100)
            vn, ve, vu = _s16(b, 40), _s16(b, 42), _s16(b, 44)
        if len(b) >= 72:
            out.update(pilot=_coord(_s32(b, 56), _s32(b, 60)), home=_coord(_s32(b, 68), _s32(b, 64)))
        if len(b) >= 73:
            out["product"] = b[72]
    else:
        if len(b) >= 52:
            out.update(alt_m=float(_s16(b, 36)), height_m=float(_s16(b, 38)), yaw_deg=_s16(b, 50) / 100)
            vn, ve, vu = _s16(b, 40), _s16(b, 42), _s16(b, 44)
        if len(b) >= 60:
            out["home"] = _coord(_s32(b, 56), _s32(b, 52))
        if len(b) >= 61:
            out["product"] = b[60]
    out["speed_h"] = math.hypot(vn, ve) / 100
    out["speed_v"] = vu / 100
    out["direction"] = None if vn == ve == 0 else (math.degrees(math.atan2(ve, vn)) + 360) % 360
    out["product_name"] = PRODUCTS.get(out.get("product"), f"DJI typ {out.get('product')}") if "product" in out else "DJI"
    return out

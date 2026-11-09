# Copyright (C) 2019 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Port na Pythona fragmentów opendroneid/opendroneid-core-c
# (libopendroneid/opendroneid.h, opendroneid.c): układ zakodowanych
# 25-bajtowych wiadomości ASTM F3411 / ASD-STAN prEN 4709-002 i reguły
# dekodowania (prędkość, wysokość, kierunek, znacznik czasu, paczka).
# Zmiany SKYGUARD (2026): przepisane na Python/struct, wynik jako dict,
# brak struktur C, dodane kodery Basic ID / Location / Pack do testów.
# Pełny tekst licencji: THIRD_PARTY_LICENSES.md.
"""Dekoder/koder wiadomości OpenDroneID (ASTM F3411)."""
from __future__ import annotations

import struct
from enum import IntEnum

MESSAGE_SIZE = 25
PACK_MAX_MESSAGES = 9
INV_TIMESTAMP = 0xFFFF
SYSTEM_EPOCH = 1546300800  # 2019-01-01 00:00:00 UTC


class MessageType(IntEnum):
    BASIC_ID = 0
    LOCATION = 1
    AUTH = 2
    SELF_ID = 3
    SYSTEM = 4
    OPERATOR_ID = 5
    PACKED = 0xF


def _txt(b: bytes) -> str:
    return b.split(b"\x00", 1)[0].decode("ascii", "replace").strip()


def _alt(enc: int):
    v = enc * 0.5 - 1000.0
    return None if v == -1000.0 else v


def _speed_h(enc: int, mult: int):
    if enc == 255:
        return None
    return enc * 0.75 + 255 * 0.25 if mult else enc * 0.25


def _dir(enc: int, ew: int):
    d = enc + (180 if ew else 0)
    return None if d > 360 else float(d)


def decode_message(msg: bytes) -> dict:
    if len(msg) < MESSAGE_SIZE:
        raise ValueError("wiadomość krótsza niż 25 B")
    msg = bytes(msg[:MESSAGE_SIZE])
    mtype, ver = msg[0] >> 4, msg[0] & 0x0F
    out: dict = {"type": MessageType(mtype) if mtype in MessageType._value2member_map_ else mtype,
                 "proto_version": ver}
    if mtype == MessageType.BASIC_ID:
        out.update(ua_type=msg[1] & 0x0F, id_type=msg[1] >> 4, uas_id=_txt(msg[2:22]))
    elif mtype == MessageType.LOCATION:
        f = msg[1]
        speed_mult, ew, height_type, status = f & 1, (f >> 1) & 1, (f >> 2) & 1, f >> 4
        direction, sp_h, sp_v, lat, lon, alt_b, alt_g, height, acc1, acc2, ts, tsacc = struct.unpack_from(
            "<BBbiiHHHBBHB", msg, 2)
        out.update(status=status, height_type=height_type,
                   direction=_dir(direction, ew), speed_h=_speed_h(sp_h, speed_mult),
                   speed_v=None if sp_v == 63 else sp_v * 0.5,
                   lat=lat / 1e7, lon=lon / 1e7,
                   alt_baro=_alt(alt_b), alt_geo=_alt(alt_g), height=_alt(height),
                   horiz_acc=acc1 & 0x0F, vert_acc=acc1 >> 4, speed_acc=acc2 & 0x0F, baro_acc=acc2 >> 4,
                   timestamp=None if ts == INV_TIMESTAMP else ts / 10.0, ts_accuracy=(tsacc & 0x0F) * 0.1)
    elif mtype == MessageType.AUTH:
        page, atype = msg[1] & 0x0F, msg[1] >> 4
        out.update(auth_type=atype, page=page)
        if page == 0:
            last, length, ts = struct.unpack_from("<BBI", msg, 2)
            out.update(last_page=last, length=length, timestamp=SYSTEM_EPOCH + ts, data=msg[8:25])
        else:
            out.update(data=msg[2:25])
    elif mtype == MessageType.SELF_ID:
        out.update(desc_type=msg[1], text=_txt(msg[2:25]))
    elif mtype == MessageType.SYSTEM:
        f = msg[1]
        op_lat, op_lon, cnt, rad, ceil, floor, cls, op_alt, ts = struct.unpack_from("<iiHBHHBHI", msg, 2)
        out.update(operator_location_type=f & 0x03, classification_type=(f >> 2) & 0x07,
                   operator_lat=op_lat / 1e7, operator_lon=op_lon / 1e7,
                   area_count=cnt, area_radius=rad * 10, area_ceiling=_alt(ceil), area_floor=_alt(floor),
                   class_eu=cls & 0x0F, category_eu=cls >> 4, operator_alt_geo=_alt(op_alt),
                   timestamp=SYSTEM_EPOCH + ts if ts else None)
    elif mtype == MessageType.OPERATOR_ID:
        out.update(operator_id_type=msg[1], operator_id=_txt(msg[2:22]))
    elif mtype == MessageType.PACKED:
        raise ValueError("paczka: użyj decode_pack()")
    return out


def decode_pack(data: bytes) -> list[dict]:
    """Paczka (typ 0xF): [nagłówek][rozmiar=25][liczba≤9][wiadomości]."""
    if len(data) < 3 or data[0] >> 4 != MessageType.PACKED:
        raise ValueError("to nie jest paczka OpenDroneID")
    size, count = data[1], data[2]
    if size != MESSAGE_SIZE or not 0 < count <= PACK_MAX_MESSAGES or len(data) < 3 + size * count:
        raise ValueError("niepoprawna paczka")
    msgs = [decode_message(data[3 + i * size:3 + (i + 1) * size]) for i in range(count)]
    counts: dict = {}
    for m in msgs:
        counts[m["type"]] = counts.get(m["type"], 0) + 1
    for t, c in counts.items():
        lim = 2 if t == MessageType.BASIC_ID else 16 if t == MessageType.AUTH else 1
        if c > lim:
            raise ValueError(f"za dużo wiadomości typu {t}")
    return msgs


def decode_any(data: bytes) -> list[dict]:
    return decode_pack(data) if data and data[0] >> 4 == MessageType.PACKED else [decode_message(data)]


# ---- kodery (do testów i symulatora) ----

def encode_basic_id(uas_id: str, id_type: int = 1, ua_type: int = 2, version: int = 2) -> bytes:
    return bytes([(MessageType.BASIC_ID << 4) | version, (id_type << 4) | ua_type]) + \
        uas_id.encode("ascii")[:20].ljust(20, b"\x00") + b"\x00" * 3


def _enc_alt(a):
    return 0 if a is None else int(round((a + 1000.0) * 2))


def encode_location(lat: float, lon: float, alt_geo: float | None = None, height: float | None = None,
                    direction: float = 0.0, speed_h: float = 0.0, speed_v: float = 0.0,
                    status: int = 2, timestamp: float | None = None, version: int = 2) -> bytes:
    ew = 1 if direction >= 180 else 0
    d = int(round(direction - 180 if ew else direction))
    if speed_h <= 255 * 0.25:
        mult, sp = 0, int(round(speed_h / 0.25))
    else:
        mult, sp = 1, min(254, int(round((speed_h - 255 * 0.25) / 0.75)))
    flags = (status << 4) | (0 << 2) | (ew << 1) | mult
    ts = INV_TIMESTAMP if timestamp is None else int(round(timestamp * 10))
    body = struct.pack("<BBbiiHHHBBHB", d, sp, int(round(speed_v / 0.5)), int(round(lat * 1e7)),
                       int(round(lon * 1e7)), _enc_alt(None), _enc_alt(alt_geo), _enc_alt(height), 0, 0, ts, 0)
    return bytes([(MessageType.LOCATION << 4) | version, flags]) + body + b"\x00"


def encode_pack(messages: list[bytes], version: int = 2) -> bytes:
    if not 0 < len(messages) <= PACK_MAX_MESSAGES:
        raise ValueError("1..9 wiadomości")
    return bytes([(MessageType.PACKED << 4) | version, MESSAGE_SIZE, len(messages)]) + b"".join(messages)

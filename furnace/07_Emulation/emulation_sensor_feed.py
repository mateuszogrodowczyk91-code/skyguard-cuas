#!/usr/bin/env python3
"""Software sensor feeder for ``SKYGUARD_EMULATION=true``.

Connects to the Blackbox TCP port and injects synthetic NMEA GPS plus decoder
telemetry so the stack has realistic traffic without USB serial hardware.

Protocol fields match ``furnace_blackbox.parse_nmea`` /
``parse_decoder_telemetry``. This feeder was written for the portfolio demo.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.skyguard_config import SkyguardSettings, configure_logging  # noqa: E402

logger = logging.getLogger("skyguard.emulation.feed")


def nmea_checksum(body: str) -> str:
    """Return the two-hex-digit NMEA XOR checksum for ``body`` (no ``$``/``*``)."""
    checksum = 0
    for ch in body:
        checksum ^= ord(ch)
    return f"{checksum:02X}"


def make_gprmc(lat: float, lon: float, utc: str | None = None) -> str:
    """Build a minimal valid ``$GPRMC`` sentence with status ``A`` (active fix)."""
    if utc is None:
        utc = time.strftime("%H%M%S", time.gmtime())

    def to_nmea(val: float, is_lat: bool) -> tuple[str, str]:
        hemi = ("N" if val >= 0 else "S") if is_lat else ("E" if val >= 0 else "W")
        aval = abs(val)
        deg = int(aval)
        minutes = (aval - deg) * 60.0
        width = 2 if is_lat else 3
        return f"{deg:0{width}d}{minutes:06.3f}", hemi

    lat_s, lat_h = to_nmea(lat, True)
    lon_s, lon_h = to_nmea(lon, False)
    body = (
        f"GPRMC,{utc},A,{lat_s},{lat_h},{lon_s},{lon_h},0.5,0.0,"
        f"{time.strftime('%d%m%y', time.gmtime())},,,"
    )
    return f"${body}*{nmea_checksum(body)}"


def make_decoder_line(freq_mhz: float, snr_db: float, tag: str = "FPV") -> str:
    """Build a decoder telemetry line compatible with Blackbox heuristics."""
    rssi = -45.0 + (snr_db - 18.0)
    return f"DEC|{tag}|FREQ:{freq_mhz:.3f} RSSI:{rssi:.1f}|TS={int(time.time())}"


async def feed(
    host: str,
    port: int,
    lat: float,
    lon: float,
    duration_s: float,
    hz: float,
) -> int:
    """Send ``duration_s`` seconds of synthetic traffic; return cycle count."""
    reader, writer = await asyncio.open_connection(host, port)
    try:
        line = await asyncio.wait_for(reader.readline(), timeout=2.0)
        if line:
            logger.info("Blackbox snapshot: %s", line.decode("utf-8", errors="replace")[:200])
    except (TimeoutError, OSError) as exc:
        logger.debug("No initial snapshot (%s)", exc)

    t0 = time.time()
    cycles = 0
    period = 1.0 / max(hz, 0.1)
    while time.time() - t0 < duration_s:
        phase = (time.time() - t0) * 0.15
        dlat = math.sin(phase) * 0.0018
        dlon = math.cos(phase) * 0.0025
        payload: dict[str, Any] = {
            "type": "emulation_feed",
            "nmea": make_gprmc(lat + dlat, lon + dlon),
            "decoder": make_decoder_line(5800.0 + random.uniform(-2, 2), 18 + random.uniform(-3, 5)),
            "uav_hint": {
                "bearing_deg": (phase * 57.3) % 360.0,
                "bpf_hz": 280 + 40 * math.sin(phase),
                "source": "software_emulation",
            },
            "ts": time.time(),
        }
        writer.write((payload["nmea"] + "\n").encode("utf-8"))
        writer.write((payload["decoder"] + "\n").encode("utf-8"))
        writer.write((json.dumps(payload) + "\n").encode("utf-8"))
        await writer.drain()
        cycles += 1
        await asyncio.sleep(period)

    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass
    logger.info("Sent %s cycles to %s:%s", cycles, host, port)
    return cycles


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    settings = SkyguardSettings.from_environ()
    parser = argparse.ArgumentParser(description="SKYGUARD emulation sensor feed")
    parser.add_argument("--host", default=settings.blackbox_host)
    parser.add_argument("--port", type=int, default=settings.blackbox_port)
    parser.add_argument("--lat", type=float, default=settings.ref_lat)
    parser.add_argument("--lon", type=float, default=settings.ref_lon)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--hz", type=float, default=2.0)
    args = parser.parse_args(argv)
    cycles = asyncio.run(feed(args.host, args.port, args.lat, args.lon, args.duration, args.hz))
    return 0 if cycles > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

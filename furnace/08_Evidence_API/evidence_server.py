#!/usr/bin/env python3
"""Minimal evidence + status HTTP API (stdlib only).

Endpoints:
  * ``GET /health``
  * ``GET /api/v1/status``
  * ``GET /api/v1/evidence``
  * ``POST /api/v1/evidence`` — append JSON; SHA-256 hash chain

Inspired by evidence-chain ideas from the GitHub laptop-agent, implemented here
without FastAPI so the furnace demo stays dependency-light.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


from lib.skyguard_config import SkyguardSettings, configure_logging  # noqa: E402

logger = logging.getLogger("skyguard.evidence")


class EvidenceStore:
    """Append-only JSON evidence log with a SHA-256 hash chain."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, rows: list[dict[str, Any]]) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(rows, handle, indent=2)
        tmp.replace(self.path)

    def items(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._read()

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = self._read()
            prev = rows[-1]["hash"] if rows else ("0" * 64)
            record: dict[str, Any] = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "prev_hash": prev,
                "payload": payload,
            }
            blob = json.dumps(record, sort_keys=True).encode("utf-8")
            record["hash"] = hashlib.sha256(blob).hexdigest()
            rows.append(record)
            self._write(rows)
            return record


def make_handler(
    store: EvidenceStore,
    status_cb: Callable[[], dict[str, Any]],
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _json(self, code: int, obj: Any) -> None:
            raw = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, fmt: str, *args: Any) -> None:
            logger.debug("HTTP " + fmt, *args)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/health":
                self._json(200, {"ok": True, "service": "skyguard-evidence"})
                return
            if path == "/api/v1/status":
                self._json(200, status_cb())
                return
            if path == "/api/v1/evidence":
                items = store.items()
                self._json(200, {"count": len(items), "items": items[-50:]})
                return
            self._json(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/api/v1/evidence":
                self._json(404, {"error": "not_found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid_json"})
                return
            if not isinstance(payload, dict):
                self._json(400, {"error": "payload_must_be_object"})
                return
            record = store.append(payload)
            self._json(201, record)

    return Handler


def build_status(settings: SkyguardSettings) -> dict[str, Any]:
    return {
        "project": "SKYGUARD / Project Furnace",
        "mode": "emulation" if settings.emulation else "live",
        "enable": {
            "blackbox": settings.enable_blackbox,
            "fusion": settings.enable_fusion,
            "pixel": settings.enable_pixel,
            "ptz": settings.enable_ptz,
        },
        "ref": {
            "lat": settings.ref_lat,
            "lon": settings.ref_lon,
            "alt": settings.ref_alt,
        },
        "blackbox_port": settings.blackbox_port,
        "ts": time.time(),
    }


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    settings = SkyguardSettings.from_environ()
    parser = argparse.ArgumentParser(description="SKYGUARD evidence API")
    parser.add_argument("--host", default=settings.evidence_host)
    parser.add_argument("--port", type=int, default=settings.evidence_port)
    parser.add_argument("--store", default=str(settings.evidence_store))
    args = parser.parse_args(argv)

    store = EvidenceStore(Path(args.store))
    handler = make_handler(store, lambda: build_status(settings))
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    logger.info("Listening on http://%s:%s", args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down evidence API")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

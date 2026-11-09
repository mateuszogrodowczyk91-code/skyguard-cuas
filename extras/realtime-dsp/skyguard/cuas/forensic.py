"""Łańcuch dowodowy (append-only JSONL, łańcuch skrótów SHA-256).

Źródło techniki: raport C-UAS (System 20 „Forensic Chain Logger”, SHA-256 + Ed25519).
Tu: łańcuch skrótów (każdy wpis zawiera skrót poprzedniego → usunięcie/zmiana wpisu
wychodzi przy weryfikacji). Podpis Ed25519 — opcjonalnie, gdy dostępny `cryptography`
(nie jest zależnością pakietu). W aplikacji Android jest osobny IncidentLogger
(SHA-256 per wpis, bez łańcucha) — ten moduł to wersja dla Centrum/laptopa.

v1.7.4 „dowody sądowe”: ten sam format (prev/hash/t/event/sig) jest JEDYNYM łańcuchem dowodowym SKYGUARD:
Cyclops Ear (tools/cyclops-ear/cyclops_ear/court) dopisuje przez ChainLog, aplikacja Android
(com.skyguard.radar.evidence.CustodyLog) pisze bajt-w-bajt ten sam skrót, a verify.py w pakiecie
dowodowym sprawdza go niezależnie. Podpis: dowolny obiekt z .sign(bytes)->bytes nad 32 bajtami skrótu
(Ed25519 z `cryptography` albo ECDSA P-256 klucza urządzenia / Android Keystore).
Pole „t” powinno być liczbą całkowitą (ms) przy wymianie z innymi językami — float zależy od formatowania.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

GENESIS = "0" * 64


def canonical(body) -> str:
    """Postać kanoniczna: posortowane klucze, bez spacji, UTF-8 bez escapowania (jak Android CustodyLog)."""
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _h(prev: str, body: dict) -> str:
    return hashlib.sha256((prev + canonical(body)).encode("utf-8")).hexdigest()


entry_hash = _h


def read(path: str):
    """Wpisy (słowniki) w kolejności zapisu; brak pliku = pusta lista."""
    try:
        with open(path, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        return []


class ChainLog:
    def __init__(self, path: str, signer=None):
        self.path, self.signer = path, signer
        self.last = GENESIS
        try:
            for line in open(path, encoding="utf-8"):
                if line.strip():
                    self.last = json.loads(line)["hash"]
        except FileNotFoundError:
            pass

    def append(self, event: dict, t: float | None = None) -> str:
        body = {"t": time.time() if t is None else t, "event": event}
        h = _h(self.last, body)
        rec = {"prev": self.last, "hash": h, **body}
        if self.signer is not None:
            rec["sig"] = self.signer.sign(bytes.fromhex(h)).hex()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.last = h
        return h


def verify(path: str, public_key=None) -> tuple[bool, int, str]:
    """Zwraca (ok, liczba_poprawnych_wpisów, komunikat)."""
    prev, n = GENESIS, 0
    for i, line in enumerate(open(path, encoding="utf-8")):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("prev") != prev:
            return False, n, f"wpis {i}: zerwany łańcuch (prev)"
        if _h(prev, {"t": r["t"], "event": r["event"]}) != r["hash"]:
            return False, n, f"wpis {i}: zmieniona treść"
        if public_key is not None and "sig" in r:
            try:
                public_key.verify(bytes.fromhex(r["sig"]), bytes.fromhex(r["hash"]))
            except Exception:
                return False, n, f"wpis {i}: zły podpis"
        prev, n = r["hash"], n + 1
    return True, n, "OK"

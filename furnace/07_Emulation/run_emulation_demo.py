#!/usr/bin/env python3
"""End-to-end software-emulation demo (no cameras, USB, or cloud billing).

Starts Blackbox + Evidence API, runs the synthetic feeder, evaluates one
synthetic target via the production engine, posts an evidence record, exits.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.skyguard_config import SkyguardSettings, configure_logging, load_env_file  # noqa: E402

logger = logging.getLogger("skyguard.emulation.demo")

BLACKBOX = _ROOT / "02_Blackbox_PS4_Linux" / "furnace_blackbox.py"
FEED = Path(__file__).with_name("emulation_sensor_feed.py")
EVIDENCE = _ROOT / "08_Evidence_API" / "evidence_server.py"
MASTER = _ROOT / "00_Master_Launcher"
LOG_DIR = _ROOT / "logs"


def wait_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _http_json(url: str, data: dict | None = None, timeout: float = 5.0) -> dict:
    # Local demo only — reject non-http(s) schemes (Semgrep B310 / urllib file://).
    if not url.startswith(("http://127.0.0.1:", "http://localhost:")):
        raise ValueError(f"Refusing non-local URL for demo HTTP client: {url!r}")
    body = None
    headers = {}
    method = "GET"
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 — scheme checked above
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    configure_logging()
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env_file = _ROOT / "config" / "skyguard.env"
    example = _ROOT / "config" / "skyguard.env.example"
    if env_file.is_file():
        load_env_file(env_file, env)
    elif example.is_file():
        load_env_file(example, env)

    # Prefer dedicated demo ports (override example file defaults for CI/local).
    # Set SKYGUARD_KEEP_ENV_PORTS=1 to respect BLACKBOX_PORT/EVIDENCE_PORT from the env file.
    if env.get("SKYGUARD_KEEP_ENV_PORTS", "").lower() not in {"1", "true", "yes"}:
        env["BLACKBOX_PORT"] = env.get("DEMO_BLACKBOX_PORT", "19090")
        env["EVIDENCE_PORT"] = env.get("DEMO_EVIDENCE_PORT", "18765")
    else:
        env.setdefault("BLACKBOX_PORT", "19090")
        env.setdefault("EVIDENCE_PORT", "18765")
    env["SKYGUARD_EMULATION"] = "true"
    env["ENABLE_BLACKBOX"] = "true"
    env["ENABLE_FUSION"] = "false"
    env["SSD_LOG_PATH"] = str(LOG_DIR / "furnace_sigint.log")
    env["EVIDENCE_STORE"] = str(_ROOT / "08_Evidence_API" / "evidence_chain.json")

    settings = SkyguardSettings.from_environ(env)
    bb_port = settings.blackbox_port
    ev_port = settings.evidence_port
    # Re-read after setdefault — Settings already captured; use env ints
    bb_port = int(env["BLACKBOX_PORT"])
    ev_port = int(env["EVIDENCE_PORT"])

    procs: list[subprocess.Popen] = []
    try:
        logger.info("Starting Blackbox on :%s", bb_port)
        procs.append(
            subprocess.Popen(
                [sys.executable, str(BLACKBOX)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        )
        logger.info("Starting Evidence API on :%s", ev_port)
        procs.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(EVIDENCE),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(ev_port),
                    "--store",
                    env["EVIDENCE_STORE"],
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        )

        if not wait_port("127.0.0.1", bb_port, 8):
            logger.error("Blackbox failed to open port %s", bb_port)
            return 1
        if not wait_port("127.0.0.1", ev_port, 8):
            logger.error("Evidence API failed to open port %s", ev_port)
            return 1

        feed = subprocess.run(
            [
                sys.executable,
                str(FEED),
                "--host",
                "127.0.0.1",
                "--port",
                str(bb_port),
                "--duration",
                "3",
                "--hz",
                "2",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if feed.stdout:
            logger.info("%s", feed.stdout.strip())
        if feed.returncode != 0:
            logger.error("Feeder failed: %s", feed.stderr)
            return feed.returncode

        sys.path.insert(0, str(MASTER))
        import numpy as np
        from skyguard_production_engine_v7 import C4ISRFusionEngine, SwarmTarget

        c4isr = C4ISRFusionEngine()
        target = SwarmTarget(
            target_id="UAV-EMU-01",
            position_enu=np.array([80.0, 120.0, 25.0]),
            velocity_enu=np.array([-25.0, -15.0, -5.0]),
            rf_signature="FPV_5.8GHz_ANALOG",
            acoustics_bpf=320.0,
            snr_db=22.0,
        )
        threat, intent, recommendation = c4isr.evaluate_threat_score(target)
        cot = c4isr.generate_cot_xml(target, threat, intent)
        payload = {
            "target_id": target.target_id,
            "threat": threat,
            "intent": intent,
            "recommendation": recommendation,
            "cot_xml_chars": len(cot),
            "mode": "emulation",
        }
        record = _http_json(f"http://127.0.0.1:{ev_port}/api/v1/evidence", data=payload)
        health = _http_json(f"http://127.0.0.1:{ev_port}/health")
        logger.info(
            "Evidence hash=%s prev=%s health=%s",
            record.get("hash"),
            record.get("prev_hash"),
            health,
        )
        logger.info("Emulation demo completed successfully")
        return 0
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.exception("Demo failed: %s", exc)
        return 1
    finally:
        for proc in procs:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

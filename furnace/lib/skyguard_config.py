"""Load SKYGUARD settings from environment and optional ``skyguard.env`` files.

No secrets are hard-coded. Paths default relative to the furnace root so the
package is portable across machines and containers.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("skyguard.config")

FURNACE_ROOT = Path(__file__).resolve().parents[1]


def _truthy(value: str, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_env_file(path: Path, environ: MutableMapping[str, str] | None = None) -> None:
    """Load KEY=VALUE lines into ``environ`` without overriding existing keys."""
    env = environ if environ is not None else os.environ
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        env.setdefault(key, value)
    logger.debug("Loaded env file %s", path)


def discover_and_load_env(environ: MutableMapping[str, str] | None = None) -> Path | None:
    """Search common locations for ``skyguard.env`` and load the first hit."""
    env = environ if environ is not None else os.environ
    explicit = env.get("SKYGUARD_ENV_FILE")
    candidates: Iterable[Path] = []
    if explicit:
        candidates = [Path(explicit)]
    else:
        candidates = [
            FURNACE_ROOT / "config" / "skyguard.env",
            FURNACE_ROOT / "config" / "skyguard.env.example",
            Path("/opt/skyguard/config/skyguard.env"),
        ]
    for path in candidates:
        if path.is_file():
            load_env_file(path, env)
            return path
    return None


@dataclass(frozen=True)
class SkyguardSettings:
    """Runtime settings for emulation / blackbox / evidence."""

    emulation: bool = True
    enable_blackbox: bool = True
    enable_fusion: bool = True
    enable_pixel: bool = False
    enable_ptz: bool = False
    blackbox_host: str = "127.0.0.1"
    blackbox_port: int = 9090
    evidence_host: str = "127.0.0.1"
    evidence_port: int = 8765
    hud_host: str = "127.0.0.1"
    hud_port: int = 9091
    ref_lat: float = 51.9851
    ref_lon: float = 5.8987
    ref_alt: float = 110.0
    ssd_log_path: Path = FURNACE_ROOT / "logs" / "furnace_sigint.log"
    evidence_store: Path = FURNACE_ROOT / "08_Evidence_API" / "evidence_chain.json"
    nodes_json: Path = FURNACE_ROOT / "config" / "nodes.json"
    # Camera placeholders only — never real credentials in the repo
    rtsp_url: str = "rtsp://CAMERA_HOST:554/stream1"
    ptz_camera_ip: str = "CAMERA_HOST"
    ptz_camera_user: str = "admin"
    ptz_camera_password: str = ""
    gemini_api_key: str = ""

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> SkyguardSettings:
        env = dict(environ or os.environ)
        discover_and_load_env(env)

        def g(key: str, default: str = "") -> str:
            return str(env.get(key, default))

        log_default = str(FURNACE_ROOT / "logs" / "furnace_sigint.log")
        store_default = str(FURNACE_ROOT / "08_Evidence_API" / "evidence_chain.json")
        nodes_default = str(FURNACE_ROOT / "config" / "nodes.json")

        return cls(
            emulation=_truthy(g("SKYGUARD_EMULATION", "true"), True),
            enable_blackbox=_truthy(g("ENABLE_BLACKBOX", "true"), True),
            enable_fusion=_truthy(g("ENABLE_FUSION", "true"), True),
            enable_pixel=_truthy(g("ENABLE_PIXEL_TRACKER", "false"), False),
            enable_ptz=_truthy(g("ENABLE_PTZ_TRACKER", "false"), False),
            blackbox_host=g("BLACKBOX_HOST", "127.0.0.1"),
            blackbox_port=int(g("BLACKBOX_PORT", "9090")),
            evidence_host=g("EVIDENCE_HOST", "127.0.0.1"),
            evidence_port=int(g("EVIDENCE_PORT", "8765")),
            hud_host=g("HUD_HOST", "127.0.0.1"),
            hud_port=int(g("HUD_PORT", "9091")),
            ref_lat=float(g("REF_LAT", "51.9851")),
            ref_lon=float(g("REF_LON", "5.8987")),
            ref_alt=float(g("REF_ALT", "110.0")),
            ssd_log_path=Path(g("SSD_LOG_PATH", log_default)),
            evidence_store=Path(g("EVIDENCE_STORE", store_default)),
            nodes_json=Path(g("SKYGUARD_NODES_JSON", nodes_default)),
            rtsp_url=g("RTSP_URL", "rtsp://CAMERA_HOST:554/stream1"),
            ptz_camera_ip=g("PTZ_CAMERA_IP", "CAMERA_HOST"),
            ptz_camera_user=g("PTZ_CAMERA_USER", "admin"),
            ptz_camera_password=g("PTZ_CAMERA_PASSWORD", ""),
            gemini_api_key=g("GEMINI_API_KEY", ""),
        )


def configure_logging(level: str = "INFO") -> None:
    """Idempotent root logging setup for CLI entrypoints."""
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(getattr(logging, level.upper(), logging.INFO))
        return
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

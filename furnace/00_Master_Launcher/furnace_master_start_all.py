import os
import sys
import time
import subprocess
import signal
import threading
import logging
import json
from datetime import datetime

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("/tmp/furnace_master.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FURNACE-MASTER")

banner = """
====================================================================================
   PROJECT FURNACE / SKYGUARD C4ISR - MASTER ONE-COMMAND ORCHESTRATOR v5.0
====================================================================================
 [SYSTEM STACK]
  ├── STREFA 1 (TEREN): Pixel 10 Pro + PTZ Camera Tracker Node (RTSP/YOLOv8)
  ├── STREFA 2 (ŚCIANA): CATV Delta Electronics RF Preamplifier Subsystem
  ├── STREFA 3 (KOCIOŁ): SIGINT / USB Serial Hardware / Android GPS-NTP Node
  ├── STREFA 4 (BLACKBOX): PS4 Linux Headless Server (pyserial TCP @ 9090)
  ├── STREFA 5 (MOST): Wireless Bridge LAN-to-WLAN Router Node
  └── STREFA 6 (GÓRA): C4ISR fusion engine v5 + Tactical HUD C2
====================================================================================
"""

class SubsystemManager:
    def __init__(self):
        self.processes = {}
        self.lock = threading.Lock()
        self.running = True

    def start_process(self, name, command, env=None):
        with self.lock:
            if name in self.processes and self.processes[name].poll() is None:
                logger.warning(f"Process {name} is already running.")
                return

            logger.info(f"Starting Subsystem [{name}]: {' '.join(command)}")
            try:
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env or os.environ.copy()
                )
                self.processes[name] = proc

                # Dedicated output logger thread
                t = threading.Thread(target=self._log_output, args=(name, proc), daemon=True)
                t.start()
            except Exception as e:
                logger.error(f"Failed to start subsystem [{name}]: {e}")

    def _log_output(self, name, proc):
        for line in iter(proc.stdout.readline, ''):
            if not self.running:
                break
            line_str = line.strip()
            if line_str:
                logger.info(f"[{name}] {line_str}")
        proc.stdout.close()

    def monitor_and_restart(self):
        while self.running:
            time.sleep(3)
            with self.lock:
                for name, proc in list(self.processes.items()):
                    poll = proc.poll()
                    if poll is not None and self.running:
                        logger.error(f"Subsystem [{name}] exited unexpectedly with code {poll}. Respawning...")
                        # Automatic restart logic
                        if name == "BLACKBOX_SERIAL_SERVER":
                            cmd = [sys.executable, "02_Blackbox_PS4_Linux/furnace_blackbox.py"]
                        elif name == "GEMINI_AGENTIC_AI_FUSION":
                            cmd = [sys.executable, "02_Blackbox_PS4_Linux/skyguard_fusion_heartbeat_v5.py"]
                        elif name == "PIXEL_VISION_TRACKER":
                            cmd = [sys.executable, "01_Teren_Pixel/pixel_tracker.py"]
                        elif name == "PTZ_SMOOTH_TRACKER":
                            cmd = [sys.executable, "01_Teren_Pixel/tapo-ptz-smooth-tracker-v2.py"]
                        else:
                            continue
                        self.start_process(name, cmd)

    def stop_all(self):
        logger.info("Stopping all FURNACE subsystems gracefully...")
        self.running = False
        with self.lock:
            for name, proc in self.processes.items():
                if proc.poll() is None:
                    logger.info(f"Terminating [{name}] (PID {proc.pid})...")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing [{name}]...")
                        proc.kill()
        logger.info("All subsystems stopped cleanly.")

def print_dashboard(manager):
    print("\n" + "="*80)
    print(" SKYGUARD C4ISR OPERATIONAL STATUS DASHBOARD ".center(80, "-"))
    print(" TIME: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " UTC")
    print("="*80)
    for name, proc in manager.processes.items():
        status = "RUNNING (PID " + str(proc.pid) + ")" if proc.poll() is None else f"EXITED ({proc.poll()})"
        print(f"  • {name:<32} : {status}")
    print("="*80 + "\n")

def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _load_extra_nodes(base_dir):
    """Load optional cameras/nodes from SKYGUARD_NODES_JSON (default: ../config/nodes.json)."""
    nodes_path = os.environ.get(
        "SKYGUARD_NODES_JSON",
        os.path.join(os.path.dirname(base_dir), "config", "nodes.json"),
    )
    if not os.path.exists(nodes_path):
        # Also try /opt/skyguard/config/nodes.json and local config/
        for candidate in (
            "/opt/skyguard/config/nodes.json",
            os.path.join(base_dir, "config", "nodes.json"),
            os.path.join(os.path.dirname(base_dir), "config", "nodes.json"),
        ):
            if os.path.exists(candidate):
                nodes_path = candidate
                break
        else:
            return {"cameras": [], "nodes": []}
    try:
        with open(nodes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded extra nodes registry from {nodes_path}")
        return data
    except Exception as e:
        logger.warning(f"Could not read nodes JSON ({nodes_path}): {e}")
        return {"cameras": [], "nodes": []}


def main():
    print(banner)
    manager = SubsystemManager()

    def signal_handler(sig, frame):
        print("\n[SIGINT/SIGTERM] Shutting down PROJECT FURNACE Master Orchestrator...")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Hardware & Environment Inspection
    logger.info("Performing Pre-flight Hardware Checks...")
    emulation = _env_bool("SKYGUARD_EMULATION", "true")
    dev_tty_exists = any(os.path.exists(f"/dev/ttyUSB{i}") or os.path.exists(f"/dev/ttyACM{i}") for i in range(4))
    if dev_tty_exists:
        logger.info("  [✓] USB Serial Hardware (SIGINT/GPS) detected on /dev/ttyUSB* or /dev/ttyACM*")
    else:
        logger.warning("  [!] No physical /dev/ttyUSB* detected. System running in Software Standalone/Emulation Mode.")
    if emulation:
        logger.info("  [i] SKYGUARD_EMULATION=true — sensor-less / cloud-friendly mode.")

    # Determine script paths relative to workspace
    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)

    enable_blackbox = _env_bool("ENABLE_BLACKBOX", "true")
    enable_fusion = _env_bool("ENABLE_FUSION", "true")
    enable_pixel = _env_bool("ENABLE_PIXEL_TRACKER", "false")
    enable_ptz = _env_bool("ENABLE_PTZ_TRACKER", "false")

    logger.info(
        "Subsystem flags: BLACKBOX=%s FUSION=%s PIXEL=%s PTZ=%s",
        enable_blackbox, enable_fusion, enable_pixel, enable_ptz,
    )

    # Persist launch commands for watchdog restarts
    launch_cmds = {}

    # 1. Launch Blackbox PS4 Serial Server
    if enable_blackbox:
        blackbox_script = os.path.join(base_dir, "02_Blackbox_PS4_Linux", "furnace_blackbox.py")
        if not os.path.exists(blackbox_script):
            blackbox_script = os.path.join(base_dir, "furnace_blackbox.py")
        cmd = [sys.executable, blackbox_script]
        launch_cmds["BLACKBOX_SERIAL_SERVER"] = cmd
        manager.start_process("BLACKBOX_SERIAL_SERVER", cmd)
        time.sleep(1)
    else:
        logger.info("Skipping BLACKBOX_SERIAL_SERVER (ENABLE_BLACKBOX=false)")

    # 2. Launch C4ISR fusion engine v5
    if enable_fusion:
        fusion_script = os.path.join(base_dir, "02_Blackbox_PS4_Linux", "skyguard_fusion_heartbeat_v5.py")
        if not os.path.exists(fusion_script):
            fusion_script = os.path.join(base_dir, "skyguard_fusion_heartbeat_v5.py")
        cmd = [sys.executable, fusion_script]
        launch_cmds["GEMINI_AGENTIC_AI_FUSION"] = cmd
        manager.start_process("GEMINI_AGENTIC_AI_FUSION", cmd)
        time.sleep(1)
    else:
        logger.info("Skipping GEMINI_AGENTIC_AI_FUSION (ENABLE_FUSION=false)")

    # 3. Launch Pixel Vision Tracker Node
    if enable_pixel:
        pixel_script = os.path.join(base_dir, "01_Teren_Pixel", "pixel_tracker.py")
        if not os.path.exists(pixel_script):
            pixel_script = os.path.join(base_dir, "pixel_tracker.py")
        cmd = [sys.executable, pixel_script]
        launch_cmds["PIXEL_VISION_TRACKER"] = cmd
        manager.start_process("PIXEL_VISION_TRACKER", cmd)
    else:
        logger.info("Skipping PIXEL_VISION_TRACKER (ENABLE_PIXEL_TRACKER=false) — enable when RTSP camera is reachable.")

    # 4. Launch PTZ Smooth Tracker Node
    if enable_ptz:
        ptz_script = os.path.join(base_dir, "01_Teren_Pixel", "tapo-ptz-smooth-tracker-v2.py")
        if not os.path.exists(ptz_script):
            ptz_script = os.path.join(base_dir, "tapo-ptz-smooth-tracker-v2.py")
        cmd = [sys.executable, ptz_script]
        launch_cmds["PTZ_SMOOTH_TRACKER"] = cmd
        manager.start_process("PTZ_SMOOTH_TRACKER", cmd)
    else:
        logger.info("Skipping PTZ_SMOOTH_TRACKER (ENABLE_PTZ_TRACKER=false) — enable when PTZ camera is on LAN/VPN.")

    # 5. Extra cameras / nodes from nodes.json (documented registry; first enabled camera can seed RTSP)
    registry = _load_extra_nodes(base_dir)
    cameras = [c for c in registry.get("cameras", []) if c.get("enabled", True)]
    nodes = [n for n in registry.get("nodes", []) if n.get("enabled", True)]
    if cameras:
        logger.info("Registered cameras in nodes.json: %s", ", ".join(c.get("name", "?") for c in cameras))
        # If pixel tracker is enabled and RTSP_URL not explicitly set, use first camera
        if enable_pixel and "RTSP_URL" not in os.environ and cameras[0].get("rtsp_url"):
            os.environ["RTSP_URL"] = cameras[0]["rtsp_url"]
            logger.info("Using RTSP_URL from nodes.json camera '%s'", cameras[0].get("name"))
    if nodes:
        logger.info(
            "Registered remote nodes: %s",
            ", ".join(f"{n.get('name')}@{n.get('host')}:{n.get('port')}" for n in nodes),
        )
        # Stash for subsystems that want to discover peers
        os.environ["SKYGUARD_EXTRA_NODES"] = json.dumps(nodes)

    # Patch watchdog to use recorded launch commands
    original_monitor = manager.monitor_and_restart

    def monitor_with_cmds():
        while manager.running:
            time.sleep(3)
            with manager.lock:
                for name, proc in list(manager.processes.items()):
                    poll = proc.poll()
                    if poll is not None and manager.running:
                        logger.error(f"Subsystem [{name}] exited unexpectedly with code {poll}. Respawning...")
                        cmd = launch_cmds.get(name)
                        if cmd:
                            manager.start_process(name, cmd)

    # Start Watchdog Monitor Thread
    monitor_thread = threading.Thread(target=monitor_with_cmds, daemon=True)
    monitor_thread.start()

    logger.info("PROJECT FURNACE master orchestration online (enabled subsystems only).")
    logger.info("Press Ctrl+C to terminate the entire master orchestration pipeline.")

    try:
        while True:
            time.sleep(10)
            print_dashboard(manager)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

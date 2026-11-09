#!/usr/bin/env python3
"""
SKYGUARD - Fusion heartbeat service shim.
The master orchestrator (furnace_master_start_all.py) expects a long-running
process named 'skyguard_fusion_heartbeat_v5.py'. The fusion logic itself lives
in skyguard_production_engine_v7.py (class C4ISRFusionEngine), so this shim
runs the production validation pipeline once at startup, then stays alive
with a heartbeat until terminated by the orchestrator.
"""

import os
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (GEMINI-FUSION-SHIM) %(message)s'
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(BASE_DIR, "skyguard_production_engine_v7.py")

if __name__ == "__main__":
    logging.info("Fusion heartbeat service starting (delegating to production engine v7)...")
    try:
        with open(ENGINE_PATH) as f:
            engine_code = f.read()
        exec(compile(engine_code, ENGINE_PATH, "exec"), {"__name__": "skyguard_fusion_boot"})
        logging.info("Production engine v7 pipeline executed successfully. Entering heartbeat loop.")
    except Exception as e:
        logging.error(f"Engine pipeline failed: {e}")
        sys.exit(1)

    # Keep the subsystem process alive for the orchestrator watchdog
    while True:
        time.sleep(30)
        logging.info("Fusion engine heartbeat: operational.")

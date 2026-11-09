#!/bin/bash
# PROJECT FURNACE / SKYGUARD C4ISR - Master Launcher Script (cloud-ready)
set -euo pipefail
echo "================================================================="
echo " Starting SKYGUARD / PROJECT FURNACE Master Orchestrator (Linux) "
echo "================================================================="
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Load cloud/local config if present
for ENVFILE in \
  "${SKYGUARD_ENV_FILE:-}" \
  /opt/skyguard/config/skyguard.env \
  "$SCRIPT_DIR/../config/skyguard.env" \
  "$SCRIPT_DIR/config/skyguard.env"
do
  if [ -n "${ENVFILE}" ] && [ -f "${ENVFILE}" ]; then
    set -a
    # shellcheck disable=SC1090
    . "${ENVFILE}"
    set +a
    echo "[config] loaded ${ENVFILE}"
    break
  fi
done

mkdir -p "$(dirname "${SSD_LOG_PATH:-/var/log/skyguard/furnace_sigint.log}")" 2>/dev/null || true
exec python3 furnace_master_start_all.py

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/furnace${PYTHONPATH:+:$PYTHONPATH}"
if [[ -n "${PYTHON:-}" && -x "${PYTHON}" ]]; then PY="$PYTHON"
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then PY="${ROOT}/.venv/bin/python"
elif [[ -x /workspace/skyguard_cloud/venv/bin/python ]]; then PY=/workspace/skyguard_cloud/venv/bin/python
else PY=python3; fi
exec "$PY" furnace/07_Emulation/run_emulation_demo.py

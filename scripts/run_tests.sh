#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/furnace${PYTHONPATH:+:$PYTHONPATH}"

pick_python() {
  if [[ -n "${PYTHON:-}" && -x "${PYTHON}" ]]; then echo "$PYTHON"; return; fi
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then echo "${ROOT}/.venv/bin/python"; return; fi
  if [[ -x /workspace/skyguard_cloud/venv/bin/python ]]; then echo /workspace/skyguard_cloud/venv/bin/python; return; fi
  command -v python3
}
PY="$(pick_python)"
echo "Using Python: $PY"
"$PY" -c "import numpy,scipy; print('numpy',numpy.__version__,'scipy',scipy.__version__)"

echo "== furnace unit tests =="
"$PY" -m unittest discover -s furnace/06_Testy_Automatyczne -v
echo "== acoustic cuas =="
"$PY" -m pytest -q extras/acoustic-cuas
echo "== realtime dsp =="
PYTHONPATH="${ROOT}/extras/realtime-dsp${PYTHONPATH:+:$PYTHONPATH}" \
  "$PY" -m pytest -q extras/realtime-dsp/skyguard/tests
echo "== emulation demo =="
"$PY" furnace/07_Emulation/run_emulation_demo.py
echo "ALL OK"

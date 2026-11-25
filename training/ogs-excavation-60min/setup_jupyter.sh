#!/usr/bin/env bash
# OGS workshop VS Code/Jupyter setup. Reuse a working Python environment first.
# No sudo, curl, internet or uv required when an existing interpreter has packages.
set -euo pipefail
cd "$(dirname "$0")"

# Override by specifying WORKSHOP_PYTHON=/absolute/path/to/python bash setup_jupyter.sh
CANDIDATES=()
if [[ -n "${WORKSHOP_PYTHON:-}" ]]; then CANDIDATES+=("$WORKSHOP_PYTHON"); fi
CANDIDATES+=(
  "/home/simoe/pip_apps/.venv-ogs/bin/python"
  "$HOME/pip_apps/.venv-ogs/bin/python"
  "$PWD/.venv-workshop/bin/python"
  "$PWD/.venv312/bin/python"
)

PY=""
for candidate in "${CANDIDATES[@]}"; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import numpy,matplotlib,meshio,scipy,vtk,pyvista,vtuIO,gmsh,ipykernel; from ogs6py import ogs' >/dev/null 2>&1; then
    PY="$candidate"
    echo "[setup] Reusing verified environment: $PY"
    break
  fi
done

if [[ -z "$PY" ]]; then
  echo "[setup] No complete existing environment detected; trying uv if already installed."
  if [[ -n "${UV:-}" && -x "$UV" ]]; then
    UV_BIN="$UV"
  elif command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
  elif [[ -x "$HOME/.local/bin/uv" ]]; then
    UV_BIN="$HOME/.local/bin/uv"
  else
    echo >&2 "ERROR: no usable Python environment and uv is not installed."
    echo >&2 "The TEC network returned HTTP 403 for the uv installer, so setup will not attempt downloads automatically."
    echo >&2 "If you have a working environment, run:"
    echo >&2 "  WORKSHOP_PYTHON=/absolute/path/to/venv/bin/python bash setup_jupyter.sh"
    exit 2
  fi
  "$UV_BIN" python install 3.12
  "$UV_BIN" venv --python 3.12 --managed-python .venv-workshop
  "$UV_BIN" pip install --python .venv-workshop/bin/python -r requirements.txt
  PY="$PWD/.venv-workshop/bin/python"
fi

echo "[setup] Python executable: $("$PY" -c 'import sys;print(sys.executable)')"
"$PY" -m ipykernel install --user --name ogs-workshop --display-name "OGS Workshop (Python 3.12)"
echo "[setup] Registered VS Code notebook kernel 'OGS Workshop (Python 3.12)'"
echo "[setup] Preflight check — external OGS binaries and existing mesh files are also checked."
if "$PY" scripts/preflight.py; then
  echo "[setup] PASS: Workshop environment and model inputs ready."
else
  echo >&2 "[setup] WARNING: At least one preflight check failed."
  echo >&2 "The kernel was registered. Resolve the reported missing tools/files before the full live run."
  exit 1
fi
echo "[setup] Open 00_environment_check.ipynb in VS Code and select 'OGS Workshop (Python 3.12)'."

#!/usr/bin/env bash
# Reuse the workshop Python kernel, print exact missing dependencies.
# No sudo, no curl, no changes to system Python.
set -euo pipefail
cd "$(dirname "$0")"

CANDIDATES=()
if [[ -n "${WORKSHOP_PYTHON:-}" ]]; then CANDIDATES+=("$WORKSHOP_PYTHON"); fi
CANDIDATES+=(
  "$HOME/pip_apps/.venv-ogs/bin/python"
  "/home/simoe/pip_apps/.venv-ogs/bin/python"
  "$PWD/.venv-workshop/bin/python"
  "$PWD/.venv-ogs/bin/python"
  "$PWD/.venv312/bin/python"
)
if command -v python >/dev/null 2>&1; then CANDIDATES+=("$(command -v python)"); fi
if command -v python3 >/dev/null 2>&1; then CANDIDATES+=("$(command -v python3)"); fi

echo "[setup] Checking available Python interpreters..."
PY=""
for candidate in "${CANDIDATES[@]}"; do
  if [[ ! -x "$candidate" ]]; then
    echo "[setup] NOT FOUND: $candidate"
    continue
  fi
  echo "[setup] FOUND: $candidate"
  if "$candidate" - <<'PYTEST'
import importlib, sys
names = ['numpy','matplotlib','meshio','scipy','vtk','pyvista','vtuIO','ogs6py.ogs','gmsh','ipykernel']
failed = []
for name in names:
    try:
        importlib.import_module(name)
    except Exception as error:
        failed.append((name, str(error)))
print(f"  Python {sys.version.split()[0]}: {sys.executable}")
for name, error in failed:
    print(f"  MISSING/BROKEN: {name}: {error}")
if not failed:
    print("  PASS: All required imports work")
raise SystemExit(bool(failed))
PYTEST
  then
    PY="$candidate"
    break
  fi
done

if [[ -z "$PY" ]]; then
  echo
  echo "ERROR: No fully working Python environment was found." >&2
  echo "The exact missing imports are printed above." >&2
  echo "If meshio reports np.string_ removed in NumPy 2, the old meshio requires NumPy 1.x." >&2
  echo "Repair the user-local Python 3.10 environment with:" >&2
  echo '  python3 -m pip install --user "numpy==1.26.4"' >&2
  echo "Then rerun this script. This changes only your user-installed NumPy, not system Python." >&2
  echo "To use an existing environment explicitly:" >&2
  echo "  WORKSHOP_PYTHON=/absolute/path/to/python bash setup_jupyter.sh" >&2
  echo "For a fully isolated environment, use virtualenv/venv where available." >&2
  echo "This script intentionally does not download uv from the blocked host." >&2
  exit 2
fi

echo "[setup] Registering workshop Jupyter kernel using $PY"
VERSION="$("$PY" -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
"$PY" -m ipykernel install --user --name ogs-workshop --display-name "OGS Workshop (Python $VERSION)"
echo "[setup] Running preflight..."
"$PY" scripts/preflight.py
echo "[setup] Open 00_environment_check.ipynb and select the OGS Workshop kernel."

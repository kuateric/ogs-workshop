#!/usr/bin/env bash
# Install a dedicated Python 3.12 VS Code/Jupyter kernel for the workshop.
# Works without sudo, Python ensurepip, or curl (Python 3 urllib bootstrap).
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

if [[ -n "${UV:-}" && -x "${UV}" ]]; then
  UV_BIN="$UV"
elif command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
  UV_BIN="$HOME/.local/bin/uv"
else
  echo "[setup] uv not found. Installing official uv launcher into user home (no sudo)."
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required to bootstrap uv without curl." >&2
    exit 2
  fi
  export UV_INSTALL_DIR="$HOME/.local/bin"
  BOOTSTRAP="$(mktemp)"
  trap 'rm -f "$BOOTSTRAP"' EXIT
  python3 - "$BOOTSTRAP" <<'PY'
import sys
import urllib.request
url = "https://astral.sh/uv/install.sh"
try:
    with urllib.request.urlopen(url, timeout=45) as response:
        script = response.read()
except Exception as exc:
    raise SystemExit(f"ERROR: could not download official uv installer: {exc}")
with open(sys.argv[1], "wb") as output:
    output.write(script)
print(f"[setup] Downloaded official uv installer ({len(script)} bytes)")
PY
  sh "$BOOTSTRAP"
  UV_BIN="$HOME/.local/bin/uv"
  if [[ ! -x "$UV_BIN" ]]; then
    echo "ERROR: uv installer completed but $UV_BIN is not executable." >&2
    exit 2
  fi
fi

echo "[setup] uv: $("$UV_BIN" --version)"
echo "[setup] Setting up isolated Python 3.12 in $ROOT/.venv-workshop"
"$UV_BIN" python install 3.12
"$UV_BIN" venv --python 3.12 --managed-python .venv-workshop
"$UV_BIN" pip install --python .venv-workshop/bin/python -r requirements.txt
.venv-workshop/bin/python -m ipykernel install --user --name ogs-workshop --display-name "OGS Workshop (Python 3.12)"

echo "[setup] Checking imports and external OGS tools"
.venv-workshop/bin/python scripts/preflight.py

echo
echo "NEXT: Open 00_environment_check.ipynb in VS Code."
echo "Select 'OGS Workshop (Python 3.12)' and run all cells."

#!/usr/bin/env bash
# Set up an isolated VS Code/Jupyter kernel without touching system Python.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
UV="${UV:-$HOME/.local/bin/uv}"
if ! command -v "$UV" >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then UV="$(command -v uv)"
  else
    echo "ERROR: uv not found. Install uv ahead of the workshop: https://docs.astral.sh/uv/getting-started/installation/"
    echo "No packages were changed."
    exit 2
  fi
fi
"$UV" python install 3.12
"$UV" venv --python 3.12 --managed-python .venv-workshop
"$UV" pip install --python .venv-workshop/bin/python -r requirements.txt gmsh
.venv-workshop/bin/python -m ipykernel install --user --name ogs-workshop --display-name "OGS Workshop (Python 3.12)"
.venv-workshop/bin/python scripts/preflight.py
echo
echo "NEXT: In VS Code open 00_environment_check.ipynb, select 'OGS Workshop (Python 3.12)', Run All."

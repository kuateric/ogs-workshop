#!/usr/bin/env python3
"""Workshop environment preflight; read-only, does not run Gmsh or OGS."""
import importlib
import importlib.metadata as metadata
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
required=["numpy","matplotlib","meshio","scipy","vtk","pyvista","vtuIO","ogs6py.ogs","gmsh","ipykernel"]
errors=[]
print("PYTHON:",sys.executable)
print("PROJECT:",ROOT)
for name in required:
    try:
        module=importlib.import_module(name)
        print(f"PASS Python: {name}")
    except Exception as exc:
        errors.append(f"Python import {name}: {exc}")
        print(f"FAIL Python: {name}: {exc}")
for binary in ("ogs","GMSH2OGS"):
    path=shutil.which(binary)
    if path:print(f"PASS command: {binary} -> {path}")
    else:
        errors.append(f"Missing command: {binary}")
        print(f"FAIL command: {binary} not on PATH")
for rel in ("geometry/excavation.geo","models/excavation.prj","01_pre_processing/01_geometry.ipynb",
            "01_pre_processing/02_meshing.ipynb","04_vscode_workflow/run_step.py"):
    path=ROOT/rel
    if path.is_file():print(f"PASS file: {rel}")
    else:errors.append(f"Missing file: {rel}");print(f"FAIL file: {rel}")

model=ROOT/"models"/"excavation.prj"
if model.is_file():
    try:
        root=ET.parse(model).getroot()
        meshes=[m.text.strip() for m in root.findall("./meshes/mesh") if m.text]
        for m in meshes:
            p=(model.parent/m).resolve()
            if p.exists():print(f"PASS mesh: {m}")
            else:errors.append(f"Missing mesh {m}");print(f"FAIL mesh: {m}")
    except Exception as exc:
        errors.append(f"Project XML: {exc}")

print()
if errors:
    print(f"PRE-FLIGHT: {len(errors)} failed checks")
    for err in errors:print(" -",err)
    raise SystemExit(1)
print("PRE-FLIGHT PASS — Python, external commands and model inputs available.")

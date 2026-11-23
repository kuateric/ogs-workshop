#!/usr/bin/env python3
"""Map GMSH2OGS boundary segments to OGS BC IDs, safely on repeated runs.

Input: the numbered GMSH2OGS outputs excavation_1.vtu etc.
Output: excavation_101.vtu (upper left), excavation_102.vtu (upper right).
Existing output meshes must not be considered new candidate inputs.
"""
from pathlib import Path
import numpy as np
import meshio

root = Path(__file__).resolve().parents[1] / "mesh"
# Ignore the script's OWN previously generated outputs: makes this step repeatable.
# Keep numbered GMSH2OGS submeshes as input; do not alter bulk excavation.vtu.
candidates = sorted(
    path for path in root.glob("excavation_*.vtu")
    if path.stem not in {"excavation_101", "excavation_102"}
)
if not candidates:
    raise SystemExit("FAIL: no GMSH2OGS boundary meshes; run step 03_subdomains first")

found = {}
for path in candidates:
    mesh = meshio.read(path)
    coords = np.asarray(mesh.points)
    if coords.size == 0 or coords.shape[1] < 2:
        continue
    if not np.all(np.abs(coords[:, 1] - 30.0) < 1e-6):
        continue
    if np.max(coords[:, 0]) <= 32.4 + 1e-6:
        key = 101
    elif np.min(coords[:, 0]) >= 32.6 - 1e-6:
        key = 102
    else:
        continue
    if key in found:
        raise SystemExit(
            f"FAIL: multiple distinct input candidates for BC {key}: "
            f"{found[key].name}, {path.name}"
        )
    if "bulk_node_ids" not in mesh.point_data:
        raise SystemExit(f"FAIL: missing bulk_node_ids in {path.name}")
    found[key] = path

for key in (101, 102):
    if key not in found:
        raise SystemExit(
            f"FAIL: BC {key} not identified; available source meshes: "
            f"{[p.name for p in candidates]}"
        )
    mesh = meshio.read(found[key])
    dest = root / f"excavation_{key}.vtu"
    meshio.write(dest, mesh)
    print(f"PASS BC {key}: {found[key].name} -> {dest.name}; {len(mesh.points)} nodes")

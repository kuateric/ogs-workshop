#!/usr/bin/env python3
"""Assign GMSH2OGS upper-left/right boundary meshes, safely on repeated runs."""
from pathlib import Path
import numpy as np
import meshio
root=Path(__file__).resolve().parents[1]/"mesh"
candidates=sorted(p for p in root.glob("excavation_*.vtu") if p.stem not in {"excavation_101","excavation_102"})
assert candidates, "Run GMSH2OGS first; numbered surface meshes missing"
found={}
for path in candidates:
    m=meshio.read(path)
    xyz=np.asarray(m.points)
    if xyz.ndim!=2 or not len(xyz) or xyz.shape[1]<2 or not np.all(abs(xyz[:,1]-30)<1e-6): continue
    if np.max(xyz[:,0]) <= 32.4+1e-6: key=101
    elif np.min(xyz[:,0]) >= 32.6-1e-6: key=102
    else: continue
    if key in found: raise RuntimeError(f"Multiple surface candidates for {key}: {found[key].name} and {path.name}")
    assert "bulk_node_ids" in m.point_data, f"Missing bulk_node_ids: {path.name}"
    found[key]=path
for key in (101,102):
    assert key in found, f"No input surface for BC {key}"
    m=meshio.read(found[key])
    meshio.write(root/f"excavation_{key}.vtu",m)
    print(f"PASS BC {key}: {found[key].name} -> excavation_{key}.vtu ({len(m.points)} nodes)")

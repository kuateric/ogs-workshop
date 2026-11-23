#!/usr/bin/env python3
"""Repair negative triangle orientations of GMSH2OGS 2-D VTU bulk mesh.

Only permutes local triangle vertices. Does not reorder bulk nodes, so
bulk_node_ids in generated boundary files remain valid.
"""
from pathlib import Path
import numpy as np
import meshio
path=Path(__file__).resolve().parents[1]/"mesh"/"excavation.vtu"
m=meshio.read(path)
count=0
found=0
for block in m.cells:
    if block.type!="triangle":
        continue
    found+=1
    xyz=m.points[block.data][:,:,:2]
    signed=(xyz[:,1,0]-xyz[:,0,0])*(xyz[:,2,1]-xyz[:,0,1])-(xyz[:,1,1]-xyz[:,0,1])*(xyz[:,2,0]-xyz[:,0,0])
    if (abs(signed)<1e-12).any():
        raise SystemExit("FAIL: zero-area triangular element")
    neg=np.flatnonzero(signed<0)
    for idx in neg:
        block.data[idx,1],block.data[idx,2]=block.data[idx,2],block.data[idx,1]
    count+=len(neg)
if found==0:
    raise SystemExit("FAIL: no triangle cells")
meshio.write(path,m)
print(f"Triangle orientation: reversed {count} negatively oriented elements")

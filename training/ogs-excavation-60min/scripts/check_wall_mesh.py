#!/usr/bin/env python3
"""Geometric checks for training mesh with a 0.2 m wide impermeable notch."""
import sys
import numpy as np
import meshio

m = meshio.read(sys.argv[1] if len(sys.argv)>1 else "mesh/excavation.msh")
p = np.asarray(m.points)
cells = [b.data for b in m.cells if b.type in ("triangle","quad")]
if not cells:
    raise SystemExit("FAIL: No 2D elements")
x0, w, toe, top = 32.5, 0.2, 8.0, 30.0
eps = 1e-7
expected = [(x0-w/2,top),(x0+w/2,top),(x0-w/2,toe),(x0+w/2,toe)]
for x,y in expected:
    count = np.count_nonzero((abs(p[:,0]-x)<eps)&(abs(p[:,1]-y)<eps))
    if count!=1:
        raise SystemExit(f"FAIL: notch vertex ({x:g},{y:g}) has {count} nodes; expected 1")

# No bulk elements may occupy the excluded wall strip above the toe.
for block in cells:
    centers = p[block][:,:,:2].mean(axis=1)
    inside = ((centers[:,0]>x0-w/2+eps)&(centers[:,0]<x0+w/2-eps)&(centers[:,1]>toe+eps))
    if inside.any():
        raise SystemExit("FAIL: elements found inside impermeable wall")
print(f"PASS: {len(p)} mesh vertices; wall notch excludes bulk cells")
print("NOTE: this geometric test does not replace OGS flux validation")

#!/usr/bin/env python3
"""Validate mesh mappings and result arrays of the OGS excavation training.

Requires: pip install meshio numpy
Usage: python scripts/check_results.py
Checks correctness of boundary-to-bulk node maps, field presence, and
Dirichlet nodal values. This does NOT prove physical water balance.
"""
from pathlib import Path
import sys
import numpy as np
import meshio

ROOT = Path(__file__).resolve().parents[1]
MESH = ROOT / "mesh"
RESULTS = ROOT / "results"

def fail(msg):
    raise SystemExit("FAIL: " + msg)

def read(path):
    if not path.exists():
        fail(f"missing {path}")
    return meshio.read(path)

bulk = read(MESH / "excavation.vtu")
n_bulk = len(bulk.points)
print(f"Bulk nodes: {n_bulk}")
for number, expected in ((101, 60.0), (102, 30.0)):
    path = MESH / f"excavation_{number}.vtu"
    boundary = read(path)
    ids = boundary.point_data.get("bulk_node_ids")
    if ids is None:
        fail(f"{path.name}: missing bulk_node_ids")
    ids = np.asarray(ids, dtype=np.int64).ravel()
    if len(ids) != len(boundary.points):
        fail(f"{path.name}: incompatible mapping length")
    if len(ids) == 0 or min(ids) < 0 or max(ids) >= n_bulk:
        fail(f"{path.name}: invalid bulk node references")
    if not np.allclose(bulk.points[ids], boundary.points, atol=1e-7, rtol=0):
        fail(f"{path.name}: coordinates disagree with bulk node mapping")
    print(f"Boundary {number}: {len(ids)} nodes, expected Dirichlet {expected:g}")

outputs = sorted(RESULTS.glob("excavation_diffusion*.vtu"))
if not outputs:
    fail("no OGS VTU output found")
out = read(outputs[-1])
pressure = out.point_data.get("pressure")
if pressure is None:
    fail("output missing nodal pressure array")
pressure = np.asarray(pressure).reshape(-1)
if len(pressure) != n_bulk:
    fail("output node count differs from original bulk mesh; inspect output")
if not np.isfinite(pressure).all():
    fail("non-finite potential values")
if pressure.min() < 30 - 1e-4 or pressure.max() > 60 + 1e-4:
    fail(f"potential out of boundary value envelope: [{pressure.min()}, {pressure.max()}]")
print(f"Potential range: [{pressure.min():.6g}, {pressure.max():.6g}]")
for number, value in ((101, 60.0), (102, 30.0)):
    ids = read(MESH / f"excavation_{number}.vtu").point_data["bulk_node_ids"]
    error = float(np.max(np.abs(pressure[np.asarray(ids, dtype=int)] - value)))
    print(f"BC {number} maximum absolute error: {error:.3e}")
    if error > 1e-5:
        fail(f"Dirichlet boundary {number} not respected")
print("PASS: mesh-node mapping and potential field checks")
print("NOTE: this is a structural/numerical smoke check, not a verified Darcy flux balance.")

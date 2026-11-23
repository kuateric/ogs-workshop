#!/usr/bin/env python3
"""Discrete FEM conservation audit for the two OGS excavation training cases.

We assemble the scalar P1 triangular element residual r = K*u with D=1.
The Dirichlet reactions are the weak-form integrated fluxes; they give
a discrete balance and are not pointwise physical Darcy fluxes.
Units: model potential * diffusion per unit out-of-plane thickness.
This does NOT establish a calibrated groundwater inflow in m3/s.
"""
from pathlib import Path
import csv
import numpy as np
import meshio

ROOT = Path(__file__).resolve().parents[1]
MESH = ROOT / "mesh"
OUT = ROOT / "results"

def get_solution(folder):
    files = list(folder.glob("excavation_diffusion_ts_1_*.vtu"))
    if len(files) != 1:
        raise RuntimeError(f"Expected exactly one final result VTU in {folder}; found {files}")
    obj = meshio.read(files[0])
    triangles = [b.data for b in obj.cells if b.type == "triangle"]
    if not triangles:
        raise RuntimeError("No triangles found in result")
    if "pressure" not in obj.point_data:
        raise RuntimeError("Missing pressure")
    return obj.points, np.vstack(triangles), np.asarray(obj.point_data["pressure"]).ravel()

def boundary_nodes(number):
    obj = meshio.read(MESH / f"excavation_{number}.vtu")
    if "bulk_node_ids" not in obj.point_data:
        raise RuntimeError(f"Boundary {number} lacks bulk_node_ids")
    ids = np.asarray(obj.point_data["bulk_node_ids"], dtype=int).ravel()
    return np.unique(ids)

def reactions(points, tris, u):
    # Signed twice-area: positive orientation is required by the OGS bulk mesh.
    x = points[tris, 0]
    y = points[tris, 1]
    twice_a = (x[:,1]-x[:,0])*(y[:,2]-y[:,0]) - (x[:,2]-x[:,0])*(y[:,1]-y[:,0])
    if np.any(twice_a <= 1.e-12):
        raise RuntimeError("Nonpositive or degenerate triangle area")
    b = np.stack([y[:,1]-y[:,2], y[:,2]-y[:,0], y[:,0]-y[:,1]], axis=1)
    c = np.stack([x[:,2]-x[:,1], x[:,0]-x[:,2], x[:,1]-x[:,0]], axis=1)
    # Element gradient = sum_i (u_i * (b_i,c_i)) / twice_area
    grad_x = np.sum(b*u[tris],axis=1)/twice_a
    grad_y = np.sum(c*u[tris],axis=1)/twice_a
    # Element reaction r_i = area * grad(N_i) dot grad(u)
    r_local = 0.5*(b*grad_x[:,None] + c*grad_y[:,None])
    r = np.zeros(len(points))
    np.add.at(r, tris.ravel(), r_local.ravel())
    return r

left = boundary_nodes(101)
right = boundary_nodes(102)
if np.intersect1d(left,right).size:
    raise RuntimeError("Dirichlet boundaries overlap")
records=[]
for label, directory, expected_left in (("bc60",OUT,60.),("bc50",OUT/"bc50",50.)):
    points,triangles,u = get_solution(directory)
    if np.max(left) >= len(u) or np.max(right) >= len(u):
        raise RuntimeError("Boundary node index exceeds solution size")
    if not np.allclose(u[left], expected_left, atol=1.e-5, rtol=0):
        raise RuntimeError(f"Dirichlet left incorrectly imposed for {label}")
    if not np.allclose(u[right],30.,atol=1.e-5,rtol=0):
        raise RuntimeError(f"Dirichlet right incorrectly imposed for {label}")
    r = reactions(points,triangles,u)
    interior = np.ones(len(points),dtype=bool)
    interior[left]=False
    interior[right]=False
    source = float(np.sum(r[left]))
    sink = float(np.sum(r[right]))
    imbalance = source+sink
    scale = max(abs(source),abs(sink),1.e-14)
    relative = abs(imbalance)/scale
    interior_max = float(np.max(np.abs(r[interior])))
    print(f"{label}: left injection={source:.12g}, right injection={sink:.12g}, "
          f"balance={imbalance:.3e}, relative={relative:.3e}, max free-DOF residual={interior_max:.3e}")
    if source <= 0 or sink >= 0:
        raise RuntimeError(f"{label}: incorrect direction of boundary reactions")
    if relative > 1.e-7 or interior_max/scale > 1.e-7:
        raise RuntimeError(f"{label}: failed discrete conservation")
    records.append(dict(case=label,left_potential=expected_left,right_potential=30,
                        left_injection=source,right_injection=sink,
                        net_imbalance=imbalance,relative_imbalance=relative,
                        max_free_dof_residual=interior_max))
# For identical, linear homogeneous problem, flux scales with BC difference (20/30).
ratio=records[1]["left_injection"]/records[0]["left_injection"]
if abs(ratio-2/3)>1.e-6:
    raise RuntimeError(f"Flux ratio {ratio} differs from expected 2/3")
out=OUT/"discrete_flux_balance.csv"
with out.open("w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(records[0]))
    w.writeheader()
    w.writerows(records)
print(f"PASS: discrete conservation and flux scaling ratio={ratio:.12g}")
print(f"Saved {out}")

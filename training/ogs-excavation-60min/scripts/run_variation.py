#!/usr/bin/env python3
"""Run a second Dirichlet case (60 -> 50) and check affine scaling.

Stationary linear diffusion with unchanged right Dirichlet value 30 implies
u_50 = 30 + (50-30)/(60-30) * (u_60 - 30) at every node.
This is an exact consequence of linearity, up to solver tolerances.
Run after bash scripts/run.sh.
"""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import numpy as np
import meshio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
OUT = ROOT / "results"
ALT = OUT / "bc50"

def solved_field(folder):
    files = sorted(folder.glob("excavation_diffusion_ts_1_*.vtu"))
    if len(files) != 1:
        raise RuntimeError(f"Expected one timestep-1 VTU in {folder}, got {files}")
    mesh = meshio.read(files[0])
    if "pressure" not in mesh.point_data:
        raise RuntimeError(f"Missing pressure array in {files[0]}")
    return mesh, np.asarray(mesh.point_data["pressure"]).reshape(-1)

def boundary_ids(tag):
    m = meshio.read(ROOT / "mesh" / f"excavation_{tag}.vtu")
    return np.asarray(m.point_data["bulk_node_ids"], dtype=int)

base, u60 = solved_field(OUT)
if np.max(np.abs(u60[boundary_ids(101)] - 60)) > 1e-5:
    raise RuntimeError("Baseline does not satisfy left boundary 60")
if np.max(np.abs(u60[boundary_ids(102)] - 30)) > 1e-5:
    raise RuntimeError("Baseline does not satisfy right boundary 30")

src = MODELS / "excavation.prj"
variant = MODELS / "excavation_bc50.generated.prj"
tree = ET.parse(src)
edited = False
for param in tree.findall("./parameters/parameter"):
    if (param.findtext("name") or "").strip() == "p_bc0":
        value = param.find("value")
        if value is None:
            raise RuntimeError("Missing value in p_bc0")
        value.text = "50"
        edited = True
if not edited:
    raise RuntimeError("p_bc0 parameter not found")
tree.write(variant, encoding="utf-8", xml_declaration=True)
ALT.mkdir(parents=True, exist_ok=True)
print("Running BC variation: left 50, right 30", flush=True)
try:
    subprocess.run(["ogs", "-o", str(ALT), str(variant)], cwd=ROOT, check=True)
finally:
    variant.unlink(missing_ok=True)

other, u50 = solved_field(ALT)
if len(u50) != len(u60) or not np.allclose(base.points, other.points, rtol=0, atol=1e-12):
    raise RuntimeError("Variation changes mesh or node ordering")
for boundary, target in ((101, 50), (102, 30)):
    err = float(np.max(np.abs(u50[boundary_ids(boundary)] - target)))
    if err > 1e-5:
        raise RuntimeError(f"Boundary {boundary} error {err:g}")

prediction = 30 + (2/3)*(u60-30)
err = float(np.max(np.abs(u50 - prediction)))
print(f"Maximum affine linearity error: {err:.9g}", flush=True)
if err > 1e-5:
    raise RuntimeError(f"Affine scaling verification failed ({err:g})")
if not (float(np.mean(u50)) < float(np.mean(u60))):
    raise RuntimeError("Expected mean potential to decrease")
blocks = [c.data for c in base.cells if c.type == "triangle"]
if not blocks:
    raise RuntimeError("Expected 2-D triangles")
tri = Triangulation(base.points[:,0], base.points[:,1], np.vstack(blocks))
fig, axs = plt.subplots(1, 2, figsize=(12,4.1), layout="constrained", sharex=True, sharey=True)
for ax,values,caption in zip(axs, (u60,u50), ("Reference: left=60", "Exercise: left=50")):
    im=ax.tricontourf(tri, values, levels=np.linspace(30,60,21), vmin=30, vmax=60)
    ax.set_title(caption)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
fig.colorbar(im, ax=axs, label="Mathematical potential [model units]")
path=OUT/"comparison_bc60_bc50.png"
fig.savefig(path, dpi=150)
plt.close(fig)
print(f"PASS: baseline vs. BC50, max difference from linear theory = {err:.4e}")
print(f"Comparison graphic: {path}")

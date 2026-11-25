#!/usr/bin/env python3
"""Rebuild presentation figures from the OGS workshop's own geometry/VTU/CSV.
No OGS numerical solve or fabricated simulation fields are used.
"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.patches import Rectangle, Polygon
from PIL import Image
import meshio

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
blue, deep = "#246080", "#18466b"

# Geometry sourced from excavation.geo, whose fixed dimensions are checked.
geo = (ROOT / "geometry" / "excavation.geo").read_text()
for token in ("L = 65;", "H = 30;", "wall_width = 0.2;", "wall_toe = 8;"):
    assert token in geo, "Unexpected geometry: " + token

verts = [(0,0),(65,0),(65,30),(32.6,30),(32.6,8),(32.4,8),(32.4,30),(0,30)]
fig, ax = plt.subplots(figsize=(12,5))
ax.add_patch(Polygon(verts, closed=True, fc="#edf5f9", ec=deep, lw=2))
ax.add_patch(Rectangle((32.4,8), 0.2,22, color="white", ec="#202f3a",lw=1.6))
ax.plot([0,32.4],[30,30],c="#bb4648",lw=5)
ax.plot([32.6,65],[30,30],c=blue,lw=5)
ax.annotate("u = 60", xy=(15,30),xytext=(11,35),color="#a53039",
            arrowprops={"arrowstyle":"->","color":"#a53039"})
ax.annotate("u = 30", xy=(49,30),xytext=(46,35),color=blue,
            arrowprops={"arrowstyle":"->","color":blue})
ax.annotate("impermeable wall", xy=(32.5,18),xytext=(38,18),arrowprops={"arrowstyle":"->"})
ax.annotate("wall toe: y = 8 m",xy=(32.5,8),xytext=(40,4),arrowprops={"arrowstyle":"->"})
ax.set_xlim(-2,67);ax.set_ylim(-2,38);ax.set_aspect("equal")
ax.set(xlabel="x [m]",ylabel="y [m]")
fig.tight_layout();fig.savefig(OUT/"geometry.png",dpi=160);plt.close(fig)

# Actual stored triangulation: no invented FE mesh.
bulk = meshio.read(ROOT / "mesh" / "excavation.vtu")
tris = np.vstack([b.data[:, :3] for b in bulk.cells if b.type == "triangle"])
fig,ax=plt.subplots(figsize=(12,4.7))
ax.triplot(bulk.points[:,0], bulk.points[:,1],tris,color="#4189ae",lw=0.48)
ax.add_patch(Rectangle((32.4,8),0.2,22,fc="white",ec="#243746",lw=1.1))
ax.set(xlim=(0,65),ylim=(0,30),xlabel="x [m]",ylabel="y [m]")
ax.set_aspect("equal");fig.tight_layout()
fig.savefig(OUT/"mesh_illustrative.png",dpi=160);plt.close(fig)

def plot_ogs(src,dst):
    mesh=meshio.read(src)
    cells=np.vstack([b.data[:,:3] for b in mesh.cells if b.type=="triangle"])
    potential=np.asarray(mesh.point_data["pressure"]).reshape(-1)
    tri=mtri.Triangulation(mesh.points[:,0],mesh.points[:,1],cells)
    fig,ax=plt.subplots(figsize=(10,5))
    contours=ax.tricontourf(tri,potential,levels=np.linspace(30,60,31),cmap="coolwarm")
    ax.tricontour(tri,potential,levels=np.arange(30,60.1,3),colors="#243746",linewidths=.45)
    v=mesh.point_data.get("v")
    if v is not None:
        # Plot real output flux vectors (no interpolation across wall void).
        xy=mesh.points[:,:2]
        stride=max(1,len(xy)//175)
        q=np.asarray(v)
        ax.quiver(xy[::stride,0],xy[::stride,1],q[::stride,0],q[::stride,1],
                  color="#075a9e",alpha=.8,scale=None,width=.002)
    ax.add_patch(Rectangle((32.4,8),.2,22,fc="white",ec="#243746",lw=1.0))
    ax.set(xlim=(0,65),ylim=(0,30),xlabel="x [m]",ylabel="y [m]")
    ax.set_aspect("equal")
    fig.colorbar(contours,ax=ax,shrink=.74,label="Potential [model units]")
    fig.tight_layout();fig.savefig(OUT/dst,dpi=155);plt.close(fig)

plot_ogs(ROOT/"results"/"excavation_diffusion_ts_1_t_1.000000.vtu","reference_flow.png")
plot_ogs(ROOT/"results"/"bc50"/"excavation_diffusion_ts_1_t_1.000000.vtu","exercise_flow.png")

with (ROOT/"results"/"discrete_flux_balance.csv").open() as f:
    rows=list(csv.DictReader(f))
assert len(rows)==2
left=[float(r["left_injection"]) for r in rows]
right=[float(r["right_injection"]) for r in rows]
fig,ax=plt.subplots(figsize=(10,4.3))
positions=np.arange(2); w=.3
ax.bar(positions-w/2,left,w,label="Left boundary reaction",color="#b64f4f")
ax.bar(positions+w/2,right,w,label="Right boundary reaction",color=blue)
ax.axhline(0,c="#1b3241",lw=1)
ax.set_xticks(positions,["Reference\n60 / 30","Exercise\n50 / 30"])
ax.set(ylabel="Integrated discrete FEM reaction [model units]")
ax.legend(frameon=False);ax.grid(axis="y",alpha=.15)
fig.tight_layout();fig.savefig(OUT/"flux_balance.png",dpi=160);plt.close(fig)

# Reuse the embedded company logo from the existing BGE TEC PowerPoint
# already tracked under presentation/. Avoid downloading brand assets.
pptx = HERE / "OGS_Excavation_Training_BGE_TEC_Template_EN.pptx"
candidates=[]
with ZipFile(pptx) as z:
    for name in z.namelist():
        if not name.startswith("ppt/media/"): continue
        try:
            img=Image.open(BytesIO(z.read(name))).convert("RGBA")
        except Exception:
            continue
        w,h=img.size
        if w<70 or h<20 or not (1.2 < w/h < 7.5): continue
        candidates.append((w*h,img,name))
assert candidates, "No suitable BGE TEC logo image found in original PPTX"
candidates.sort(key=lambda x:x[0], reverse=True)
# Most prominent landscape-format graphic in the original presentation template.
_,logo,origin=candidates[0]
logo.save(OUT/"bge_tec_logo.png")
print("Logo extracted from original template:",origin)
print("All presentation assets recreated from workshop files.")

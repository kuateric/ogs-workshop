#!/usr/bin/env python3
"""Numerical plots from real Gmsh and OGS files; no OGSTools required."""
from pathlib import Path
import sys, re, csv
import numpy as np, meshio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parent
FIG=ROOT/"results"/"figures";FIG.mkdir(parents=True,exist_ok=True)
def mesh(name):return meshio.read(ROOT/"mesh"/name)
def triangles(m):
    t=np.vstack([c.data for c in m.cells if c.type=="triangle"])
    return t,mtri.Triangulation(m.points[:,0],m.points[:,1],t)
def frame(ax,title):
    ax.set(xlim=(0,65),ylim=(0,30),xlabel="x [m]",ylabel="y [m]",title=title)
    ax.set_aspect("equal")
def main(step):
    fig,ax=plt.subplots(figsize=(11,5))
    if step=="geometry":
        source=(ROOT/"geometry"/"excavation.geo").read_text()
        def p(k):return float(re.search(r"^"+k+r"\s*=\s*([0-9.]+)\s*;",source,re.M).group(1))
        L,H,x,w,toe=[p(k) for k in ("L","H","wall_x","wall_width","wall_toe")]
        ax.add_patch(Rectangle((0,0),L,H,facecolor="#dbeafe",edgecolor="#334155"))
        ax.add_patch(Rectangle((x-w/2,toe),w,H-toe,facecolor="white",edgecolor="black"))
        ax.annotate("Excluded wall region",xy=(x,toe),xytext=(x+5,toe+5),arrowprops={"arrowstyle":"->"})
        frame(ax,"Geometry from excavation.geo")
    elif step=="mesh":
        m=mesh("excavation.msh");t,tri=triangles(m)
        ax.triplot(tri,color="#64748b",lw=.38)
        frame(ax,f"Gmsh 2-D mesh: {len(m.points)} nodes; {len(t)} triangles")
    elif step=="material":
        m=mesh("excavation.vtu");t,tri=triangles(m)
        ids=np.concatenate([np.asarray(arr).ravel() for arr,cell in zip(m.cell_data["MaterialIDs"],m.cells) if cell.type=="triangle"])
        assert np.array_equal(np.unique(ids),[0]),"Unexpected material IDs"
        ax.tripcolor(tri,facecolors=ids,edgecolors="#94a3b8",linewidth=.2,cmap="Blues",vmin=-.5,vmax=.5)
        frame(ax,f"MaterialIDs: only material 0 ({len(t)} triangles)")
    elif step in ("boundaries","setup"):
        m=mesh("excavation.vtu");_,tri=triangles(m)
        ax.triplot(tri,color="#cbd5e1",lw=.25)
        for key,value,color in [(101,60,"#be123c"),(102,30,"#1d4ed8")]:
            b=mesh(f"excavation_{key}.vtu")
            ids=np.asarray(b.point_data["bulk_node_ids"]).astype(int)
            assert np.allclose(b.points,m.points[ids],atol=1e-7)
            ax.scatter(b.points[:,0],b.points[:,1],s=20,color=color,label=f"BC {key}, potential {value}")
        ax.legend();frame(ax,"OGS boundary submeshes: top left/right")
    elif step in ("solution","comparison","flow"):
        files=sorted((ROOT/"results").glob("excavation_diffusion_ts_1_*.vtu"))
        assert files,"Reference OGS result missing"
        m=meshio.read(files[-1]);_,tri=triangles(m)
        vals=np.asarray(m.point_data["pressure"]).reshape(-1)
        levels=np.linspace(30,60,31)
        cs=ax.tricontourf(tri,vals,levels=levels,cmap="coolwarm")
        ax.tricontour(tri,vals,levels=np.arange(30,60.1,2.5),colors="#242a37",linewidths=.55)
        if step=="flow" and "v" in m.point_data:
            from scipy.interpolate import griddata
            gx=np.linspace(0,65,220);gy=np.linspace(0,30,110);X,Y=np.meshgrid(gx,gy)
            v=np.asarray(m.point_data["v"])
            vx=griddata(m.points[:,:2],v[:,0],(X,Y));vy=griddata(m.points[:,:2],v[:,1],(X,Y))
            bad=(tri.get_trifinder()(X,Y)<0)|(~np.isfinite(vx))|(~np.isfinite(vy))
            ax.streamplot(gx,gy,np.ma.masked_where(bad,vx),np.ma.masked_where(bad,vy),density=1.2,color="#005b96",linewidth=.7)
        ax.add_patch(Rectangle((32.4,8),.2,22,facecolor="white",edgecolor="black",zorder=10))
        fig.colorbar(cs,ax=ax,label="Potential [model units]")
        frame(ax,"Reference potential"+(" and model-flux streamlines" if step=="flow" else ""))
    elif step=="balance":
        with (ROOT/"results"/"discrete_flux_balance.csv").open() as f: rows=list(csv.DictReader(f))
        ax.bar(np.arange(len(rows))-.15,[float(r["left_injection"]) for r in rows],width=.3,label="left reaction")
        ax.bar(np.arange(len(rows))+.15,[float(r["right_injection"]) for r in rows],width=.3,label="right reaction")
        ax.set_xticks(np.arange(len(rows)),[r["case"] for r in rows])
        ax.legend();ax.set_ylabel("FEM reaction [model units]");ax.set_title("Discrete flux balance")
    else: raise SystemExit("Unknown plot step: "+step)
    out=FIG/(step+".png");fig.savefig(out,dpi=170,bbox_inches="tight");plt.close(fig)
    print("PLOT:",out)
if __name__=="__main__": main(sys.argv[1])

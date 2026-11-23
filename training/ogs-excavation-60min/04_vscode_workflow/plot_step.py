#!/usr/bin/env python3
"""Generate honest annotated diagnostics from the actual source geometry and OGS results."""
from pathlib import Path
import sys, csv, re
import numpy as np
import meshio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'figures';OUT.mkdir(parents=True,exist_ok=True)


def triangulation(mesh):
    tris=np.vstack([c.data for c in mesh.cells if c.type=='triangle'])
    return tris, Triangulation(mesh.points[:,0], mesh.points[:,1], tris)

def frame(ax,title):
    ax.set(xlim=(0,65),ylim=(0,30),xlabel='x [m]',ylabel='y [m]',title=title)
    ax.set_aspect('equal')

def save(fig,name):
    path=OUT/(name+'.png');fig.savefig(path,dpi=175,bbox_inches='tight');plt.close(fig)
    print('PLOT:',path)

def sol(folder):
    paths=sorted(folder.glob('excavation_diffusion_ts_1_*.vtu'))
    assert len(paths)==1,f'Expected exactly one solved final VTU: {paths}'
    return meshio.read(paths[0])

def material(ax):
    m=meshio.read(ROOT/'mesh'/'excavation.vtu'); t,tri=triangulation(m)
    arrays=m.cell_data['MaterialIDs']; ids=np.concatenate([np.asarray(a).ravel() for a,c in zip(arrays,m.cells) if c.type=='triangle'])
    assert len(ids)==len(t)
    ax.tripcolor(tri,facecolors=ids,vmin=-0.5,vmax=0.5,cmap='Blues',edgecolors='#64748b',linewidth=0.13)
    frame(ax,f'One material region: MaterialID 0, {len(t)} triangles')
    assert np.array_equal(np.unique(ids),[0])
    return m,tri

def boundaries(ax):
    m=meshio.read(ROOT/'mesh'/'excavation.vtu');t,tri=triangulation(m)
    ax.triplot(tri,lw=0.22,color='#cbd5e1')
    for tag,value,color in [(101,60,'#be123c'),(102,30,'#1d4ed8')]:
        b=meshio.read(ROOT/'mesh'/f'excavation_{tag}.vtu')
        ids=np.asarray(b.point_data['bulk_node_ids']).astype(int)
        assert np.allclose(b.points,m.points[ids],atol=1e-7)
        ax.scatter(b.points[:,0],b.points[:,1],s=19,color=color,label=f'BC {tag}: u={value} ({len(ids)} nodes)')
    ax.legend(loc='lower center',framealpha=0.95)
    frame(ax,'Actual OGS Dirichlet boundary meshes on bulk mesh')

def contours(ax,mesh,title,levels=None):
    tris,tri=triangulation(mesh)
    levels=np.linspace(30,60,31) if levels is None else levels
    vals=np.asarray(mesh.point_data['pressure']).reshape(-1)
    cf=ax.tricontourf(tri,vals,levels=levels,cmap='coolwarm')
    ax.tricontour(tri,vals,levels=np.arange(30,60.01,2.5),colors='black',linewidths=0.38,alpha=0.4)
    ax.add_patch(Rectangle((32.4,8),0.2,22,facecolor='white',edgecolor='#334155',zorder=10,lw=1))
    frame(ax,title)
    return cf

def main(name):
    if name=='geometry':
        content=(ROOT/'geometry'/'excavation.geo').read_text()
        def par(s):return float(re.search(r'^'+s+r'\s*=\s*([0-9.]+)\s*;',content,re.M).group(1))
        L,H,x,w,toe=[par(k) for k in ('L','H','wall_x','wall_width','wall_toe')]
        fig,ax=plt.subplots(figsize=(11,5))
        ax.add_patch(Rectangle((0,0),L,H,facecolor='#dbeafe',edgecolor='#0f172a'))
        ax.add_patch(Rectangle((x-w/2,toe),w,H-toe,facecolor='white',edgecolor='#334155'))
        ax.annotate('Wall void (not soil)',xy=(x,toe),xytext=(x+4,toe+4),arrowprops={'arrowstyle':'->'})
        frame(ax,'Geometry from excavation.geo — before meshing');save(fig,'01_geometry')
    elif name=='mesh':
        m=meshio.read(ROOT/'mesh'/'excavation.msh');t,tri=triangulation(m)
        fig,ax=plt.subplots(figsize=(11,5));ax.triplot(tri,color='#64748b',lw=0.35)
        frame(ax,f'Gmsh P1 triangle mesh: {len(m.points)} nodes, {len(t)} triangles');save(fig,'02_meshing')
    elif name=='material':
        fig,ax=plt.subplots(figsize=(11,5));material(ax);save(fig,'03_materials')
    elif name in ('boundaries','setup'):
        fig,ax=plt.subplots(figsize=(11,5));boundaries(ax);save(fig,'04_boundaries' if name=='boundaries' else '05_setup')
    elif name=='solution':
        fig,ax=plt.subplots(figsize=(11,5));cf=contours(ax,sol(ROOT/'results'),'Reference: u_left=60, u_right=30')
        fig.colorbar(cf,ax=ax,label='Potential [model units]');save(fig,'06_reference')
    elif name in ('comparison','flow'):
        m60=sol(ROOT/'results');m50=sol(ROOT/'results'/'bc50')
        fig,axs=plt.subplots(2,1,figsize=(11,10),layout='constrained')
        for ax,m,left in zip(axs,[m60,m50],[60,50]):
            cf=contours(ax,m,f'Left {left} / right 30: potential and equipotentials')
            if name=='flow':
                from scipy.interpolate import griddata
                _,tri=triangulation(m)
                v=m.point_data.get('v')
                if v is not None:
                    gx=np.linspace(0,65,230);gy=np.linspace(0,30,110);X,Y=np.meshgrid(gx,gy)
                    vx=griddata(m.points[:,:2],np.asarray(v)[:,0],(X,Y))
                    vy=griddata(m.points[:,:2],np.asarray(v)[:,1],(X,Y))
                    mask=(tri.get_trifinder()(X,Y)<0) | (~np.isfinite(vx)) | (~np.isfinite(vy))
                    ax.streamplot(gx,gy,np.ma.masked_where(mask,vx),np.ma.masked_where(mask,vy),
                                  density=1.1,color='#005b96',linewidth=.65,arrowsize=.7)
        fig.colorbar(cf,ax=axs,shrink=.65,label='Potential [model units]')
        save(fig,'08_flow_network' if name=='flow' else '07_comparison')
    elif name=='balance':
        with (ROOT/'results'/'discrete_flux_balance.csv').open() as f:rows=list(csv.DictReader(f))
        x=np.arange(len(rows));fig,ax=plt.subplots(figsize=(8,4))
        for off,key,color,label in [(-.18,'left_injection','#be123c','Left reaction'),(.18,'right_injection','#1d4ed8','Right reaction')]:
            ax.bar(x+off,[float(r[key]) for r in rows],width=.36,color=color,label=label)
        ax.set_xticks(x,[r['case'] for r in rows]);ax.set_ylabel('Discrete FEM reactions [model units]')
        ax.set_title('Discrete conservation: equal and opposite boundary reactions')
        ax.legend();ax.axhline(0,color='black',lw=.7);save(fig,'09_balance')
    else:
        raise SystemExit('Unknown plot step: '+name)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python plot_step.py geometry|mesh|material|boundaries|setup|solution|comparison|flow|balance')
    main(sys.argv[1])

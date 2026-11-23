#!/usr/bin/env python3
"""Standalone 9-step OGS workshop runner; no notebook required."""
from pathlib import Path
import subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
def run(*args):
    cmd=[str(a) for a in args];print("RUN:"," ".join(cmd),flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)
def step(i):
    if i==1:
        assert (ROOT/"geometry"/"excavation.geo").exists()
        run(sys.executable,"plot_step.py","geometry")
    elif i==2:
        try:import gmsh
        except ImportError:raise SystemExit("Install gmsh in this interpreter")
        (ROOT/"mesh").mkdir(exist_ok=True)
        gmsh.initialize()
        try:
            gmsh.open(str(ROOT/"geometry"/"excavation.geo"))
            gmsh.option.setNumber("Mesh.MshFileVersion",2.1)
            gmsh.model.mesh.generate(2)
            gmsh.write(str(ROOT/"mesh"/"excavation.msh"))
        finally:gmsh.finalize()
        run(sys.executable,"scripts/check_wall_mesh.py","mesh/excavation.msh")
        run(sys.executable,"plot_step.py","mesh")
    elif i==3:
        run("GMSH2OGS","-i","mesh/excavation.msh","-o","mesh/excavation.vtu","-e","-b")
        run(sys.executable,"scripts/orient_bulk_mesh.py")
        run(sys.executable,"plot_step.py","material")
    elif i==4:
        run(sys.executable,"scripts/assign_boundary_meshes.py")
        run(sys.executable,"plot_step.py","boundaries")
    elif i==5:
        doc=ET.parse(ROOT/"models"/"excavation.prj")
        par={p.findtext("name"):p.findtext("value") for p in doc.findall("./parameters/parameter")}
        assert par.get("p_bc0")=="60" and par.get("p_bc1")=="30"
        print("Model parameters:",par)
        run(sys.executable,"plot_step.py","setup")
    elif i==6:
        (ROOT/"results").mkdir(exist_ok=True)
        run("ogs","-o","results","models/excavation.prj")
        run(sys.executable,"scripts/check_results.py")
        run(sys.executable,"plot_step.py","solution")
    elif i==7:run(sys.executable,"scripts/run_variation.py")
    elif i==8:run(sys.executable,"plot_step.py","flow")
    elif i==9:
        run(sys.executable,"scripts/check_results.py")
        run(sys.executable,"scripts/check_flux_balance.py")
        run(sys.executable,"plot_step.py","balance")
    else:raise ValueError(i)
    print(f"PASS Step {i}")
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("python run_step.py 1..9|all")
    if sys.argv[1]=="all":
        for i in range(1,10):step(i)
    else:step(int(sys.argv[1]))

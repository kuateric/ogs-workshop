#!/usr/bin/env python3
"""Generate the course Gmsh mesh from the command line using the active Python kernel.

Usage: python3 scripts/generate_mesh_cli.py geometry/excavation.geo terminal_mesh_output/excavation.msh
"""
import sys
from pathlib import Path
import gmsh

if len(sys.argv) != 3:
    raise SystemExit("Usage: python3 scripts/generate_mesh_cli.py INPUT.geo OUTPUT.msh")
geometry = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
if not geometry.is_file():
    raise SystemExit(f"Missing geometry file: {geometry}")
output.parent.mkdir(parents=True, exist_ok=True)
gmsh.initialize()
try:
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.open(str(geometry))
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.1)
    gmsh.model.mesh.generate(2)
    gmsh.write(str(output))
finally:
    gmsh.finalize()
assert output.is_file() and output.stat().st_size > 0, "Mesh not generated"
print(f"PASS: generated Gmsh 2.1 mesh: {output}")

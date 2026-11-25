# Command-line mesh generation — NUMO 60-minute course

Open **VS Code Terminal** in `training/ogs-excavation-60min/`.

The following operations reproduce Steps **2 (meshing), 3 (bulk conversion), 4 (boundary extraction)** without running notebooks. Outputs are isolated in `terminal_mesh_output/` and cannot overwrite the normal `mesh/` notebook files.

## Step 2 — Gmsh

```bash
mkdir -p terminal_mesh_output
python3 scripts/generate_mesh_cli.py geometry/excavation.geo terminal_mesh_output/excavation.msh
python3 scripts/check_wall_mesh.py terminal_mesh_output/excavation.msh
```

Alternatively (only if the `gmsh` executable is correctly installed on PATH):

```bash
gmsh -2 geometry/excavation.geo -format msh2 -o terminal_mesh_output/excavation.msh
```

## Step 3 — Gmsh to OpenGeoSys

```bash
GMSH2OGS -i terminal_mesh_output/excavation.msh -o terminal_mesh_output/excavation.vtu -e -b
python3 scripts/orient_bulk_mesh.py terminal_mesh_output
```

## Step 4 — top Dirichlet boundary surfaces

```bash
python3 scripts/assign_boundary_meshes.py terminal_mesh_output
ls -lh terminal_mesh_output/excavation.vtu terminal_mesh_output/excavation_101.vtu terminal_mesh_output/excavation_102.vtu
```

Expected outputs: `excavation.msh`, `excavation.vtu`, various numbered GMSH2OGS 1D submeshes, and `excavation_101.vtu` (top-left) / `excavation_102.vtu` (top-right). The latter two retain `bulk_node_ids`, mapping each boundary node to a bulk mesh node.

`python3` must be the interpreter where `gmsh`, `numpy`, and `meshio` were installed. `GMSH2OGS` must be on PATH. The dedicated output folder is excluded from Git.

These meshes are for the **terminal demonstration**, not the default simulation path. The existing OGS project `models/excavation.prj` uses meshes in `mesh/`. To run OGS with these alternative meshes, the project mesh paths would need to be adapted separately.

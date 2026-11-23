# OGS Excavation Hands-on — clean training edition

Two clearly separated ways to run the same benchmark:

## A. Teaching / Jupyter in VS Code

Open the root folder in VS Code. Select the tested clean Jupyter kernel (`/home/simoe/pip_apps/.venv-ogs/bin/python`). Run one notebook at a time, in numerical order:

- `01_pre_processing/01_geometry.ipynb` — source geometry; white slit is excluded material
- `01_pre_processing/02_meshing.ipynb` — triangles and refinement at wall tip
- `01_pre_processing/03_subdomains.ipynb` — bulk mesh and real `MaterialIDs`: **one region, ID 0**
- `01_pre_processing/04_surfaces.ipynb` — separate left/right Dirichlet boundary submeshes
- `02_processing/05_model_setup.ipynb` — OGS XML parameters and actual boundary mapping
- `02_processing/06_run_reference.ipynb` — solve 60/30 reference case
- `02_processing/07_run_exercise.ipynb` — solve 50/30 exercise case
- `03_post_processing/08_flow_network.ipynb` — streamline/equipotential plots
- `03_post_processing/09_verification.ipynb` — nodal BCs and discrete FEM conservation

Read **Explain → Run → Visualize → PASS** in each notebook. Generated plots and VTUs are based on actual files. Do not interpret model units as kPa or m/s.

## B. Normal workflow in VS Code terminal (NO JUPYTER)

Open `04_vscode_workflow/README.md`. This independent folder contains all source geometry, OGS project files, helper scripts, `run_step.py`, and local `mesh/` + `results/` output directories. Run `python run_step.py 1` ... `python run_step.py 9`, or `bash run_all.sh`. External OGS binaries `ogs` and `GMSH2OGS` must be on PATH; Python must provide `gmsh`, `meshio`, `numpy`, `matplotlib`, `scipy`.

## Clean-up / retained files

Old `notebooks/legacy/` notebooks, redundant static images, and obsolete launcher `scripts/run.sh` were removed. Root `geometry/`, `models/`, `scripts/`, `mesh/` and `results/` remain for the Jupyter path. Solved VTUs are kept to allow Post-processing demonstrations when computation is unavailable. The CLI workflow is intentionally self-contained; its inputs duplicate the minimal required source files, not generated results.

**Scientific note:** `MaterialID = 0` for all 1,236 triangles. This is one 2D material, not a multi-material subdomain benchmark. `excavation_101`/`_102` are 1D boundary meshes, not independent material regions.

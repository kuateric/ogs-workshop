# OGS excavation — 60-minute hands-on workshop

**Main project:** This directory adds the structured workshop to the existing `kuateric/ogs-workshop` repository without replacing the root installer.

## Learning workflow
- `01_pre_processing/`: Step 1 geometry, Step 2 mesh, Step 3 material-domain tagging, Step 4 boundary submeshes
- `02_processing/`: Step 5 project setup, Step 6 reference simulation, Step 7 boundary variation
- `03_post_processing/`: Step 8 potential/flux streamline plot, Step 9 FEM flux balance
- `04_vscode_workflow/`: self-contained source and terminal workflow; no notebooks needed

## VS Code / terminal
```bash
cd training/ogs-excavation-60min/04_vscode_workflow
python -m pip install -r ../requirements.txt
python run_step.py all
```
Use a Python venv, or `uv pip install -r ../requirements.txt`. Requires `ogs` and `GMSH2OGS` commands on PATH. Run individual steps with `python run_step.py 1` ... `python run_step.py 9`.

## Jupyter
Open the repository in VS Code, choose your verified Python kernel and run the nine numbered notebooks **in order**. Notebooks call the exact same `04_vscode_workflow/run_step.py` used from the terminal and display the corresponding computed plots. This avoids divergent results.

## Scientific interpretation
- Geometry: 65 m x 30 m with a 0.2 m wide excluded wall strip from y=8 to y=30 m.
- Single bulk material: `MaterialIDs=0` for all 1,236 triangles in the reference mesh.
- Dirichlet potentials: 60/30 and 50/30; values are mathematical model units, not calibrated kPa.
- Exported flux vector v is a model flux, not calibrated m/s.
- The mesh path in both project files is **`../mesh/` relative to their models directory**. Never prepend `04_vscode_workflow/` inside `models/excavation.prj`.
- Results and mesh files are generated on demand; the repository contains source and repeatable execution scripts. Native validation must be performed in the target OGS environment.

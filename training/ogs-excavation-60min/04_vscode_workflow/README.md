# Standalone VS Code / Terminal Workflow (no Jupyter)

This folder is **self-contained**. It contains `geometry/`, `models/`, `scripts/`, `run_step.py`, `plot_step.py`; generated `mesh/` and `results/` remain inside this same folder. **Do not run notebooks here.**

## Setup in the VS Code integrated terminal

Use the already working Python interpreter `/home/simoe/pip_apps/.venv-ogs/bin/python` or another clean Python >= 3.11 with `numpy<2`, `meshio`, `matplotlib`, `scipy`, `gmsh`. External commands `ogs` and `GMSH2OGS` must be available on PATH; they are OGS binaries, not Python packages. **No OGSTools required.**

```bash
cd 04_vscode_workflow
source /home/simoe/pip_apps/.venv-ogs/bin/activate
python -c 'import gmsh, meshio, numpy, matplotlib; print("Python OK")'
command -v ogs
command -v GMSH2OGS
python run_step.py 1
python run_step.py 2
python run_step.py 3
python run_step.py 4
python run_step.py 5
python run_step.py 6
python run_step.py 7
python run_step.py 8
python run_step.py 9
```

Or: `bash run_all.sh` (runs all steps in order). Each step prints `PASS` and writes images under `results/figures/` in this folder.

## Calculation stages

1. Geometry: geometry `.geo` input and preview PNG
2. Meshing: Gmsh Python API creates `.msh` (avoids broken `/usr/local/bin/gmsh` launcher)
3. Conversion: `GMSH2OGS`, normalise mesh orientation, plot single material region ID 0
4. Boundary mappings: produce and validate `excavation_101.vtu`, `excavation_102.vtu`
5. Model setup: inspect actual `.prj` values and show boundary nodes on mesh
6. Reference OGS solve: write VTUs to `results/`, validate BCs and plot potential
7. Exercise OGS solve: left value 50 in temporary variant, verify exact 2/3 scaling
8. Postprocessing: equi-potentials and streamlines from exported OGS arrays
9. Discrete FEM reactions: check conservation and plot signed boundary balance

**Use case:** scripted engineering work and repeatable command-line calculation. Jupyter in `01_`–`03_` is for teaching/learning; this folder is for normal calculation practice. The independent workflow always rebuilds from its own input files.

**Note:** The original workshop uses a mathematical diffusion coefficient equal to 1. Its pressure and flux data are **model units**, not calibrated kPa, m/s or m3/s. `MaterialID=0` is one single material region.

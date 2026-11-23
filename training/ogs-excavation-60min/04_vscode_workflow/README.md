# Standalone VS Code workflow

This directory contains all required **source files** (geometry, model, and scripts) independent of Jupyter. Generated meshes/results are deliberately excluded from Git; run steps in sequence to recreate them.

```bash
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

Or `bash run_all.sh`. Use the correct isolated Python and ensure `ogs` and `GMSH2OGS` are available. The fixed mesh references in models/excavation.prj are relative to models/, hence ../mesh/.

Outputs: `mesh/`, `results/`, `results/figures/`.

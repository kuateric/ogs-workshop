# OGS Excavation — participant exercises (English)

## 60-minute agenda

| Time | Run in VS Code Jupyter | Explain / observed output |
| --- | --- | --- |
| 0–5 min | `01_pre_processing/01_geometry.ipynb` | Geometry 65 × 30 m; thin, impermeable wall void |
| 5–12 min | `01_pre_processing/02_meshing.ipynb` | Triangular mesh with refinement at wall toe |
| 12–18 min | `01_pre_processing/03_subdomains.ipynb` | One material region, MaterialID = 0 |
| 18–25 min | `01_pre_processing/04_surfaces.ipynb` | Dirichlet 1D boundary submeshes 101, 102 |
| 25–31 min | `02_processing/05_model_setup.ipynb` | `.prj` XML model inputs, actual mesh with BC values |
| 31–38 min | `02_processing/06_run_reference.ipynb` | OGS reference solution (60/30) |
| 38–45 min | `02_processing/07_run_exercise.ipynb` | OGS exercise solution (50/30) |
| 45–54 min | `03_post_processing/08_flow_network.ipynb` | Equipotentials and model flux streamlines |
| 54–60 min | `03_post_processing/09_verification.ipynb` | Discrete FEM conservation and 2/3 scaling |

**Normal engineering work without notebooks:** use `04_vscode_workflow/README.md` and execute `python run_step.py 1` through `9`, or `bash run_all.sh`. This folder has its own complete sources and keeps its output separate from teaching notebooks.

## Questions

1. Why does the bulk mesh have **only MaterialID = 0**? Because this is a single-material example: subdomain tagging does not automatically create multiple materials.
2. What is the difference between `excavation.vtu` and `excavation_101.vtu`? The first is the complete bulk mesh; the second is the left Dirichlet boundary submesh with `bulk_node_ids`.
3. What changes when the left boundary potential is reduced from 60 to 50? The potential and flux amplitudes scale with the imposed difference: `20/30 = 2/3`.
4. Are flux values m³/s? **No**: this numerical diffusion benchmark has not been parameterised as real groundwater flow.

Use the green PASS messages as specific numerical checks, not a general claim of validation.

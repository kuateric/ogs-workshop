# NUMO: 10-minute OGSTools demo (Python 3.10, TEC shell)

**Notebook:** `00_OGSTools_Quick_Demo.ipynb`.

This is a short four-code-cell version of the original excavation example using `ogstools==0.7.1` (supports Python 3.10). The latest `ogstools==0.8.2` requires Python >=3.11 and has a substantially different API.

## Environment check

Use your existing terminal and Jupyter kernel, which previously ran Python 3.10.12 with OpenGeoSys on PATH:

```bash
python3 --version
python3 -c "import ogstools; print('OGSTools available:', ogstools.__version__)"
command -v ogs
```

If OGSTools is not installed, and access to your Python package index works:

```bash
python3 -m pip install --user "ogstools==0.7.1" "numpy>=1.26,<2"
```

Avoid `sudo pip` and `--break-system-packages`. User-local pip installation may still affect other user-local Python packages. Prefer a separate preconfigured virtualenv if available. The previously blocked `astral.sh` UV installer is **not** required.

Open `00_OGSTools_Quick_Demo.ipynb` in VS Code, choose the Python interpreter where `import ogstools` works, then **Run All**.

## Scope of the live demo

This notebook uses the course's precomputed `mesh/excavation.vtu` and `models/excavation.prj`. It does **not** redo Gmsh generation or boundary extraction. It runs the OGS solver and plots its new result using OGSTools. Four code cells replace the previous nine notebooks; more extensive teaching materials remain intact.

**Files created locally only:** `models/quick_demo.prj`, `quick_demo_results/`.

This notebook was checked against the documented OGSTools 0.7.x interfaces. A complete `Run All` has **not yet been verified on the TEC machine**, so do a dry run before presenting.

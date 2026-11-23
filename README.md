# OpenGeoSys Workshop — Ubuntu 24.04 / 26.04

A reproducible, self-contained training environment for **OpenGeoSys (OGS)**, **Intel oneMKL/PARDISO**, **TFEL/MFront**, **Gmsh**, and scientific Python post-processing.

**Platform:** Ubuntu 24.04 or 26.04 LTS, x86-64. Recommended: at least **16 GB RAM**, **60 GB of free disk space**, reliable internet access, and **sudo** privileges. Building OGS and VTK from source is CPU- and disk-intensive. The OGS source revision is pinned for reproducibility.

## 1. Quick installation

No GitHub account or authentication is required:

```bash
git clone https://github.com/kuateric/ogs-workshop.git
cd ogs-workshop
bash install.sh --dry-run
bash install
```

The `bash install` launcher defaults to **7 parallel compilation jobs** and uses the isolated directory `~/ogs-workshop-test/environment`. To adjust parallelism, run `OGS_WORKSHOP_JOBS=2 bash install` on low-memory machines.

The full installation includes:

1. **Ubuntu prerequisites:** GCC/GFortran, CMake 3.31.10, Ninja, Git, Python build dependencies, HDF5, Boost, Eigen and graphics libraries.
2. **Gmsh:** the system CLI/GUI, development headers and Python API. A 2D mesh-generation and meshio-readback test is included.
3. **Intel oneAPI:** oneMKL, PARDISO and Intel OpenMP, installed from Intel's signed APT repository. A numerical 2×2 PARDISO solver check is included.
4. **TFEL/MFront:** source build from the `rliv-5.1` branch, including the interface used by OGS.
5. **OpenGeoSys:** pinned revision `8ffec079b9ce8764ab565c6470839b34033bc718` from [upstream OGS](https://gitlab.opengeosys.org/ogs/ogs); all processes, CLI utilities, MFront, MKL and XDMF enabled.
6. **Python environment:** Python 3.12 in a dedicated virtual environment, with OGSTools, ogs6py, VTUinterface, PyVista, VTK, NumPy, SciPy, Pandas, Matplotlib, meshio, Gmsh, h5py, Plotly and JupyterLab.
7. **Desktop tools:** ParaView from Ubuntu APT and Visual Studio Code from Microsoft's signed repository.
8. **Verification:** binary/package checks, generated Gmsh mesh, VTU roundtrip, OGS project XML creation, PARDISO solve and actual short OGS reference simulations.

**System changes:** `--all` installs or updates system packages and APT sources. OGS and TFEL builds are placed in a separate user-owned directory; existing OGS source/build folders are not deleted. Do not disable APT signature checks.

## 2. Using the environment

After a successful installation:

```bash
source ~/ogs-workshop-test/environment/activate.sh
which ogs
ogs --help
gmsh --version
mfront --version
python -c "import ogstools, ogs6py, vtuIO, pyvista, matplotlib; print('Python OK')"
jupyter lab ~/ogs-workshop-test/environment/notebooks/01_ogs_diffusion_analysis.ipynb
```

Activation sets `OGS_BIN_PATH` to the locally compiled OGS binary and `LD_LIBRARY_PATH` for Intel and TFEL runtime libraries.

Additional commands, from the cloned `ogs-workshop` repository directory:

```bash
bash install.sh --verify   # Check tools and Python integration, without rebuilding
bash install.sh --smoke    # Run representative OGS calculations and Python checks
```

When invoking `install.sh` directly after using `bash install`, preserve the same environment directory:

```bash
export OGS_WORKSHOP_HOME="$HOME/ogs-workshop-test/environment"
bash install.sh --smoke
```

Reports and test results are written under `~/ogs-workshop-test/environment/results/`:

- `verification.json`: machine-readable PASS/FAIL report
- `cases/<case>/ogs.log`: captured solver logs
- `cases/<case>/`: generated OGS results
- `gmsh_unit_square.msh`: generated Gmsh mesh
- `python_roundtrip.vtu` and `python_roundtrip.png`: Python IO/plot demo
- `ogs6py_generated_project.prj`: XML generation demonstration (not a complete simulation project)

## 3. Verification coverage

| Process or tool | Test | Success criterion |
|---|---|---|
| Gmsh CLI/Python | Mesh a 2D square, read MSH using meshio | Nonempty nodes and elements |
| Intel PARDISO | Solve a 2×2 linear system | Solution `(2,2)`, error code 0 |
| Steady-state diffusion | Upstream OGS reference case | Exit 0, nonempty outputs |
| PardisoLU diffusion | Same case with solver override | Exit 0, nonempty outputs |
| Small deformation | Upstream mechanical reference case | Exit 0, nonempty outputs |
| Richards flow | Upstream flow reference case | Exit 0, nonempty outputs |
| Hydro-mechanics | Upstream coupled reference case | Exit 0, nonempty outputs |
| Thermo-Richards flow | Upstream 2D reference case | Exit 0, nonempty outputs |
| Thermo-Richards mechanics | Upstream TRM reference case | Exit 0, nonempty outputs |
| TH2M | Upstream TH2M reference case | Exit 0, nonempty outputs |
| ogs6py | Generate a valid XML project file | XML parses successfully |
| PyVista / meshio / VTUinterface / Matplotlib | VTU roundtrip and image | Valid data and nonempty files |
| OGSTools | Import and check OGS integration | Correct binary path |

These are **representative process-family checks**, not exhaustive validation of all OGS C++ classes, MFront material laws, or long-duration coupled simulations.

For a focused verification run:

```bash
export OGS_WORKSHOP_HOME="$HOME/ogs-workshop-test/environment"
source "$OGS_WORKSHOP_HOME/activate.sh"
python verify.py --models --only steady_diffusion --only small_deformation \
  --ogs "$OGS_BIN_PATH/ogs" \
  --source "$OGS_WORKSHOP_HOME/src/ogs/Tests/Data" \
  --output "$OGS_WORKSHOP_HOME/results"
```

## 4. Troubleshooting

- **APT fails:** Repair the signed package repository; never use `--allow-unauthenticated`.
- **Intel OpenMP missing:** Check that `libiomp5.so` is installed and available via `activate.sh`.
- **MFront not found by CMake:** Run `bash install.sh --tfel`, then `bash install.sh --ogs` using the correct `OGS_WORKSHOP_HOME`.
- **VTK compilation appears slow:** Inspect CPU activity and the build log before assuming the build has stalled.
- **Wrong OGS executable:** Inspect `echo "$OGS_BIN_PATH"`.
- **ParaView or VS Code cannot open:** GUI applications require a desktop session; headless installation checks do not validate GUI launches.
- **Python packages unavailable in the system interpreter:** Activate the workshop venv rather than using `sudo pip`.

## 5. Official references

- [OpenGeoSys](https://www.opengeosys.org/stable/docs/devguide/getting-started/prerequisites/)
- [OGS source](https://gitlab.opengeosys.org/ogs/ogs)
- [TFEL/MFront](https://thelfer.github.io/tfel/web/install.html)
- [Intel oneMKL](https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl-download.html)
- [OGSTools](https://ogstools.opengeosys.org/stable/user-guide/)
- [ogs6py](https://github.com/joergbuchwald/ogs6py)
- [VTUinterface](https://github.com/joergbuchwald/VTUinterface)
- [Gmsh](https://gmsh.info/)
- [ParaView](https://www.paraview.org/Download/)
- [VS Code](https://code.visualstudio.com/docs/setup/linux)

## Release status

Ubuntu 24.04 and 26.04 support is configured, but the full fresh-installation path (including GUI applications) has **not yet been verified end-to-end on Ubuntu 26.04**. The full installation requires system-level APT changes and must be run with suitable privileges. This is a community training project, not an official OGS distribution.

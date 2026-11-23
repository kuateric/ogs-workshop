#!/usr/bin/env python3
"""Reproducible OGS workshop verification: Python packages, IO and real OGS runs.

Tests use upstream OGS Tests/Data projects from the EXACT checked out OGS commit.
Never claims every OGS C++ class is exercised; each selected process family has
its own real simulation. No expected output is fabricated or overwritten.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

# Small, existing upstream reference cases. The program checks their process
# <type> before execution, and fails if any file is absent or changes family.
CASES = {
    "steady_diffusion": {
        "path": "Elliptic/square_1x1_SteadyStateDiffusion/square_1e0.prj",
        "type": "STEADY_STATE_DIFFUSION",
    },
    "pardiso_steady_diffusion": {
        "path": "Elliptic/square_1x1_SteadyStateDiffusion/square_1e0.prj",
        "type": "STEADY_STATE_DIFFUSION",
        "solver_override": "PardisoLU",
    },
    "small_deformation": {
        "path": "Mechanics/EvaluatingBbarWithSimpleExamples/simple_b_bar_test.prj",
        "type": "SMALL_DEFORMATION",
    },
    "richards_flow": {
        "path": "HydroMechanics/StaggeredScheme/FlowFullySaturated/flow_fully_saturated.prj",
        "type": "RICHARDS_FLOW",
    },
    "hydro_mechanics": {
        "path": "HydroMechanics/Linear/Confined_Compression/square_1e2_tri.prj",
        "type": "HYDRO_MECHANICS",
    },
    "thermo_richards_flow": {
        "path": "ThermoRichardsFlow/RichardsFlow2D/RichardsFlow_2d_small.prj",
        "type": "THERMO_RICHARDS_FLOW",
    },
    "thermo_richards_mechanics": {
        "path": "ThermoRichardsMechanics/LinearMechanics/mechanics_linear.prj",
        "type": "THERMO_RICHARDS_MECHANICS",
    },
    "th2m": {
        "path": "TH2M/TotalInitialStress/total_initial_stress_H2M.prj",
        "type": "TH2M",
    },
}

MODULES = {
    "ogstools": "ogstools",
    "ogs6py": "ogs6py",
    "VTUinterface": "vtuIO",
    "numpy": "numpy",
    "scipy": "scipy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "PyVista": "pyvista",
    "VTK": "vtk",
    "meshio": "meshio",
    "gmsh": "gmsh",
    "h5py": "h5py",
    "lxml": "lxml",
    "PyYAML": "yaml",
    "xarray": "xarray",
    "netCDF4": "netCDF4",
    "sympy": "sympy",
    "pint": "pint",
    "Shapely": "shapely",
    "scikit-learn": "sklearn",
    "Plotly": "plotly",
    "Seaborn": "seaborn",
    "Pillow": "PIL",
    "imageio": "imageio",
    "JupyterLab": "jupyterlab",
    "notebook": "notebook",
    "ipykernel": "ipykernel",
    "ipywidgets": "ipywidgets",
    "pytest": "pytest",
    "rich": "rich",
    "tqdm": "tqdm",
}

def record(report: dict, category: str, name: str, ok: bool, detail: str = "") -> None:
    value = {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}
    report[category].append(value)
    print(f"[{value['status']}] {category}: {name}" + (f" – {detail}" if detail else ""), flush=True)


def check_modules(report: dict) -> None:
    for label, mod in MODULES.items():
        try:
            m = importlib.import_module(mod)
            version = str(getattr(m, "__version__", "imported"))
            record(report, "python", label, True, version)
        except Exception as exc:
            record(report, "python", label, False, f"{type(exc).__name__}: {exc}")


def check_ogs6py(report: dict, output: Path) -> None:
    try:
        from ogs6py import ogs
        path = output / "ogs6py_generated_project.prj"
        m = ogs.OGS(PROJECT_FILE=str(path))
        m.mesh.add_mesh(filename="example_mesh.vtu")
        m.write_input()
        r = ET.parse(path).getroot()
        assert r.find(".//mesh") is not None, "missing generated mesh reference"
        record(report, "python_io", "ogs6py XML project generation", True, str(path))
    except Exception as exc:
        record(report, "python_io", "ogs6py XML project generation", False,
               f"{type(exc).__name__}: {exc}")


def check_python_mesh_roundtrip(report: dict, output: Path) -> None:
    try:
        import numpy as np
        import pyvista as pv
        import meshio
        import vtuIO
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0]], dtype=float)
        cells = np.array([3, 0, 1, 2], dtype=np.int64)
        celltypes = np.array([pv.CellType.TRIANGLE], dtype=np.uint8)
        grid = pv.UnstructuredGrid(cells, celltypes, pts)
        grid.point_data["temperature"] = np.array([273.15, 283.15, 293.15])
        vtu = output / "python_roundtrip.vtu"
        grid.save(vtu)
        mesh = meshio.read(vtu)
        assert len(mesh.points) == 3, "meshio incorrect point count"
        assert "temperature" in mesh.point_data, "missing point field in meshio"

        vtui = vtuIO.VTUIO(str(vtu), dim=2)
        fields = vtui.get_point_field_names()
        assert "temperature" in fields, f"VTUinterface missing field: {fields}"
        temp = vtui.get_point_field("temperature")
        assert len(temp) == 3, "VTUinterface field length mismatch"

        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], np.asarray(temp), "o-")
        ax.set(xlabel="Node", ylabel="Temperature (K)",
               title="OGS Workshop: PyVista → VTUinterface → Matplotlib")
        png = output / "python_roundtrip.png"
        fig.savefig(png, dpi=110)
        plt.close(fig)
        assert vtu.stat().st_size > 0 and png.stat().st_size > 0
        record(report, "python_io", "PyVista + VTK + meshio + VTUinterface + Matplotlib", True,
               f"VTU={vtu.name}, PNG={png.name}")
    except Exception as exc:
        record(report, "python_io", "PyVista + VTK + meshio + VTUinterface + Matplotlib",
               False, f"{type(exc).__name__}: {exc}")


def check_ogstools(report: dict, ogs_bin: Path) -> None:
    try:
        import ogstools as ot
        assert hasattr(ot, "Project"), "ogstools.Project unavailable"
        # ogstools.status() is diagnostic-only and returns None on some
        # versions; a None return is NOT an installation failure.
        status = ot.status(verbose=False)
        selected_bin = os.environ.get("OGS_BIN_PATH", "")
        assert selected_bin, "OGS_BIN_PATH not set"
        assert (Path(selected_bin) / "ogs").resolve() == ogs_bin.resolve(), (
            f"OGSTools OGS_BIN_PATH points to a different OGS: {selected_bin}"
        )
        record(report, "python_io", "OGSTools Project + environment status",
               True, f"OGS_BIN_PATH={selected_bin}; diagnostic_return={type(status).__name__}")
    except Exception as exc:
        record(report, "python_io", "OGSTools Project + environment status", False,
               f"{type(exc).__name__}: {exc}")


def check_gmsh(report: dict, output: Path) -> None:
    """Exercise the system CLI and Python API with an actual generated mesh."""
    try:
        import gmsh
        cli = shutil.which("gmsh")
        assert cli, "Gmsh CLI not installed; run bash install.sh --gmsh"
        version = subprocess.run([cli, "--version"], capture_output=True,
                                 text=True, timeout=20, check=True)
        assert (version.stdout + version.stderr).strip(), "Empty Gmsh version"
        mesh = output / "gmsh_unit_square.msh"
        gmsh.initialize(["-nopopup"])
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.model.add("workshop_square")
            p1 = gmsh.model.geo.addPoint(0, 0, 0, 0.25)
            p2 = gmsh.model.geo.addPoint(1, 0, 0, 0.25)
            p3 = gmsh.model.geo.addPoint(1, 1, 0, 0.25)
            p4 = gmsh.model.geo.addPoint(0, 1, 0, 0.25)
            edges = [gmsh.model.geo.addLine(a, b) for a, b in
                     [(p1, p2), (p2, p3), (p3, p4), (p4, p1)]]
            loop = gmsh.model.geo.addCurveLoop(edges)
            surface = gmsh.model.geo.addPlaneSurface([loop])
            gmsh.model.geo.synchronize()
            gmsh.model.addPhysicalGroup(2, [surface], name="domain")
            gmsh.model.mesh.generate(2)
            node_tags, _, _ = gmsh.model.mesh.getNodes()
            types, _, element_tags = gmsh.model.mesh.getElements(2)
            assert len(node_tags) > 4 and sum(map(len, element_tags)) > 0
            gmsh.write(str(mesh))
        finally:
            gmsh.finalize()
        assert mesh.is_file() and mesh.stat().st_size > 0
        import meshio
        readback = meshio.read(mesh)
        assert len(readback.points) > 4
        record(report, "python_io", "Gmsh CLI + Python 2D mesh + meshio readback",
               True, f"version={version.stdout.strip()}; nodes={len(readback.points)}; mesh={mesh}")
    except Exception as exc:
        record(report, "python_io", "Gmsh CLI + Python 2D mesh + meshio readback",
               False, f"{type(exc).__name__}: {exc}")


def check_binary(report: dict, ogs_bin: Path) -> None:
    try:
        assert ogs_bin.is_file() and os.access(ogs_bin, os.X_OK), str(ogs_bin)
        cp = subprocess.run([str(ogs_bin), "--help"], text=True, capture_output=True, timeout=35)
        assert cp.returncode == 0, (cp.stdout + cp.stderr)[-900:]
        record(report, "binaries", "OpenGeoSys executable --help", True, str(ogs_bin))
    except Exception as exc:
        record(report, "binaries", "OpenGeoSys executable --help", False,
               f"{type(exc).__name__}: {exc}")


def run_case(report: dict, name: str, item: dict, source: Path,
             ogs_bin: Path, output: Path, timeout_seconds: int) -> None:
    prj = source / item["path"]
    dest = output / "cases" / name
    dest.mkdir(parents=True, exist_ok=True)
    log = dest / "ogs.log"
    try:
        assert prj.is_file(), f"Upstream sample missing: {prj}"
        process_types = [(e.text or "").strip()
                         for e in ET.parse(prj).getroot().findall(".//processes/process/type")]
        assert item["type"] in process_types, f"Wrong process type: {process_types}"
        # For a real OGS/Eigen PARDISO integration test: replace the solver in
        # an isolated COPY of the upstream reference project, never the source.
        run_project = prj
        if item.get("solver_override"):
            input_folder = dest / "input"
            shutil.copytree(prj.parent, input_folder, dirs_exist_ok=True)
            run_project = input_folder / prj.name
            xml = ET.parse(run_project)
            eigen_nodes = xml.getroot().findall(".//linear_solvers/linear_solver/eigen")
            assert eigen_nodes, "Upstream reference has no Eigen solver to override"
            for node in eigen_nodes:
                setting = node.find("solver_type")
                if setting is None:
                    setting = ET.SubElement(node, "solver_type")
                setting.text = item["solver_override"]
            xml.write(run_project, encoding="utf-8", xml_declaration=True)
            assert item["solver_override"] in run_project.read_text()
        started = time.monotonic()
        cp = subprocess.run(
            [str(ogs_bin), str(run_project), "-o", str(dest)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            timeout=timeout_seconds, cwd=str(run_project.parent), check=False)
        elapsed = round(time.monotonic() - started, 2)
        log.write_text(cp.stdout)
        assert cp.returncode == 0, f"exit={cp.returncode}; log={log}; tail={cp.stdout[-350:]}"
        outputs = list(dest.glob("*.vtu")) + list(dest.glob("*.pvd")) + list(dest.glob("*.xdmf"))
        # A successful process exit is not sufficient for a workshop exercise:
        # every selected reference model must produce at least one result file.
        assert outputs, f"OGS returned exit 0 but produced no VTU/PVD/XDMF results; log={log}"
        assert all(p.stat().st_size > 0 for p in outputs), (
            f"One or more OGS result files are empty; log={log}"
        )
        detail = f"{item['type']}, {elapsed}s, outputs={len(outputs)}, log={log}"
        record(report, "ogs_cases", name, True, detail)
    except subprocess.TimeoutExpired as exc:
        record(report, "ogs_cases", name, False,
               f"timeout>{timeout_seconds}s; prj={prj}")
    except Exception as exc:
        record(report, "ogs_cases", name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", action="store_true", help="Import and exercise Python packages")
    parser.add_argument("--models", action="store_true", help="Run real reference OGS simulations")
    parser.add_argument("--ogs", type=Path, required=True, help="Full absolute path to compiled ogs")
    parser.add_argument("--source", type=Path, required=True,
                        help="OGS source Tests/Data path from the same compiled commit")
    parser.add_argument("--output", type=Path, required=True, help="Write outputs and JSON report")
    parser.add_argument("--timeout", type=int, default=90,
                        help="Maximum seconds for each OGS sample (default: 90)")
    parser.add_argument("--only", choices=list(CASES), action="append",
                        help="Run only named OGS process family; repeat as needed")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ["OGS_BIN_PATH"] = str(args.ogs.parent.resolve())
    report = {"metadata": {
        "python": sys.version.split()[0],
        "ogs": str(args.ogs.resolve()), "source": str(args.source.resolve()),
        "mode": {"packages": args.packages, "models": args.models},
        "timestamp_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
    }, "binaries": [], "python": [], "python_io": [], "ogs_cases": []}

    check_binary(report, args.ogs)
    if args.packages:
        check_modules(report)
        check_ogs6py(report, args.output)
        check_gmsh(report, args.output)
        check_python_mesh_roundtrip(report, args.output)
        check_ogstools(report, args.ogs)
    if args.models:
        for name in (args.only or list(CASES)):
            run_case(report, name, CASES[name], args.source, args.ogs,
                     args.output, args.timeout)

    report_path = args.output / "verification.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    failed = [f"{k}/{item['name']}" for k in ("binaries", "python", "python_io", "ogs_cases")
              for item in report[k] if item["status"] == "FAIL"]
    print(f"\nRESULT: {len(failed)} failures; JSON={report_path}", flush=True)
    if failed:
        for name in failed:
            print("FAILED", name, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

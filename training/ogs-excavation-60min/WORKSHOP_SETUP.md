# Start-of-meeting setup (Linux, VS Code)

1. **Prefer installing before the meeting**, while internet is working.
2. Clone the repository and open `training/ogs-excavation-60min` in VS Code.
3. From VS Code terminal: `bash setup_jupyter.sh` (requires preinstalled `uv`; does not modify system Python).
4. Open `00_environment_check.ipynb` and select **OGS Workshop (Python 3.12)**.
5. Run All. Confirm all green PASS lines and the plotted OGS potential field.
6. If all attendees use different laptops, provide `ogs` and `GMSH2OGS` separately; this setup only installs Python packages.

For the instructor's existing tested environment (`/home/simoe/pip_apps/.venv-ogs/bin/python`), simply select that kernel and run the notebook. The provided setup creates a separate `.venv-workshop` when needed.

**Do not install packages into system Python** or use `--break-system-packages`.

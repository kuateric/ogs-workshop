# OGS-Schulung: vollständige Linux-Umgebung (Ubuntu 24.04 / 26.04)

**Ziel:** Alle Teilnehmenden erhalten eine vergleichbare Umgebung für OpenGeoSys,
Intel oneMKL/PARDISO, TFEL/MFront sowie Python-Vor- und Nachverarbeitung.

**Plattform:** Ubuntu **24.04 / 26.04 LTS, x86-64**, GNU C++ 13 oder neuer. Empfohlen:
**16+ GB RAM, 60+ GB freier Speicher**, stabiler Internetzugang und **sudo**
für Systempakete. OGS/VTK aus Quellcode benötigt viel Rechenzeit. Für ein
vollständig gleiches Trainingsmodell bitte dieselbe Version dieses Ordners
verwenden; die OGS-Version ist per Commit festgelegt.

## 1. Installation für Kollegen

Das Repository öffentlich ohne Anmeldung klonen und in den Ordner wechseln:\n\n```bash\ngit clone https://github.com/kuateric/ogs-workshop.git\ncd ogs-workshop\n```\n\nDann ausführen:

```bash
bash install.sh --dry-run
bash install
```

Das Skript installiert nacheinander:

1. **Ubuntu-Build-Voraussetzungen:** Compiler/GFortran, CMake 3.31.10,
   Ninja, Git, Python 3.12, HDF5, Boost, Eigen und Grafikbibliotheken.
2. **Gmsh:** Systemprogramm `gmsh` (CLI und GUI) sowie `libgmsh-dev` aus Ubuntu-APT. Zusätzlich steht die Gmsh-Python-API im Workshop-Venv bereit. Ein 2D-Rechteck wird automatisch vernetzt und als `.msh` über `meshio` wieder eingelesen.
3. **Intel oneAPI Toolkit (2026):** oneMKL-Entwicklungspaket inklusive
   PARDISO und Intel OpenMP. Die Intel-Pakete stammen aus dem signierten
   offiziellen Intel-APT-Repository. Der PARDISO-Test löst ein
   kleines lineares System mit erwarteter Lösung `(2,2)`.
4. **TFEL/MFront:** frische Quellcode-Kompilierung aus dem stabilen
   `rliv-5.1`-Zweig der TFEL-5.1-Familie mit Generic Interface für OGS.
5. **OpenGeoSys:** Commit
   `8ffec079b9ce8764ab565c6470839b34033bc718` von
   `gitlab.opengeosys.org/ogs/ogs`, Release-Build aller Prozesse
   (`OGS_BUILD_PROCESSES=ON`), `OGS_USE_MFRONT=ON`,
   `OGS_USE_MKL=ON`, MKL-Eigen-Backend, XDMF und CLI-Tools.
6. **Python-Venv:** `ogstools`, `ogs6py`, `VTUinterface` (`import vtuIO`),
   PyVista, VTK, NumPy, SciPy, Matplotlib, Pandas, meshio, Gmsh,
   h5py, JupyterLab, Plotly und weitere Analysepakete.
7. **Desktop:** ParaView (Ubuntu-APT-Paket) und Visual Studio Code
   (offiziell signiertes Microsoft-APT-Repository).
8. **Automatische Prüfungen:** Imports, VTU-Roundtrip, generiertes XML,
   ein numerischer PARDISO-Test und echte kurze OGS-Referenzsimulationen.

**Wichtig:** Bei `--all` werden Systempakete und APT-Repositories installiert.
Das Skript lässt bestehende OGS-Verzeichnisse unangetastet und installiert
die selbst gebauten Programme ausschließlich unter
`~/ogs-workshop/`. Es setzt keine Root-Rechte für den OGS-Build ein.
Wenn eine APT-Quelle auf dem Rechner kaputt ist, bricht es sicher ab;
APT-Signaturprüfungen dürfen nicht deaktiviert werden.

## 2. Nutzung im Unterricht

Nach erfolgreicher Installation:

```bash
source ~/ogs-workshop/activate.sh
which ogs
ogs --help
which mfront
mfront --version
python -c "import ogstools, ogs6py, vtuIO, pyvista, matplotlib; print('Python OK')"
jupyter lab ~/ogs-workshop/notebooks/01_ogs_diffusion_auswertung.ipynb
```

Das Aktivierungsskript setzt insbesondere **`OGS_BIN_PATH`** auf das
selbst gebaute OGS mit MKL und **`LD_LIBRARY_PATH`** auf die Intel-
und TFEL-Bibliotheken. Damit wird nicht versehentlich der OGS-Python-Wheel
anstelle des gewünschten MKL-Builds benutzt.

Weitere Kommandos:

```bash
bash install.sh --verify   # nur prüfen, kein Neubau
bash install.sh --smoke    # echte OGS-Rechnungen + Python-Auswertung prüfen
```

Das beigefügte Jupyter-Notebook `notebooks/01_ogs_diffusion_auswertung.ipynb` führt durch einen echten OGS-Diffusionsfall, vergleicht PyVista mit VTUinterface, erstellt einen Matplotlib-Plot und ermöglicht den numerischen Vergleich mit einem OGS-PardisoLU-Lauf.

Die Ergebnisse werden unter `~/ogs-workshop/results/` abgelegt:

- `verification.json`: maschinenlesbare PASS/FAIL-Liste
- `cases/<prozess>/ogs.log`: vollständiges OGS-Protokoll je Referenzfall
- `cases/<prozess>/`: Resultate der einzelnen OGS-Rechnungen
- `gmsh_unit_square.msh`: generiertes 2D-Testnetz aus Gmsh\n- `python_roundtrip.vtu` und `python_roundtrip.png`: Python-Demotest
- `ogs6py_generated_project.prj`: XML-Generator-Demodatei (nicht als
  vollständiges ausführbares OGS-Modell gedacht)

## 3. Schulungstests

| Prozess-/Werkzeugklasse | Test | Nachweiskriterium |
|---|---|---|
| Gmsh CLI + Python-API | 2D-Einheitsquadrat erzeugen und als MSH mit meshio einlesen | Nichtleeres Netz, gültige Knoten/Elemente |\n| Intel MKL/PARDISO | 2×2 lineares System | Lösung `(2,2)`, Fehlercode 0 |
| OGS-Steady-State-Diffusion | `Elliptic/square_1x1_SteadyStateDiffusion` | OGS exit 0 |
| Small Deformation | `Mechanics/EvaluatingBbarWithSimpleExamples` | OGS exit 0 |
| Richards Flow | `HydroMechanics/StaggeredScheme/FlowFullySaturated` | OGS exit 0 |
| Hydro-Mechanics | `HydroMechanics/Linear/Confined_Compression` | OGS exit 0 |
| Thermo-Richards-Mechanics | `ThermoRichardsMechanics/LinearMechanics` | OGS exit 0 |
| Thermo-Richards-Flow | `ThermoRichardsFlow/RichardsFlow2D/RichardsFlow_2d_small.prj` | OGS exit 0, nichtleere Ergebnisdateien |
| TH2M | `TH2M/TotalInitialStress` | OGS exit 0 |
| Python/ogs6py | XML-Projektgenerierung | Datei erzeugt, XML gültig |
| PyVista + VTK + meshio + VTUinterface + Matplotlib | VTU speichern/lesen, PNG plotten | Feld und Dateien korrekt |
| OGSTools | Module und Projekt-API | Python-Import und OGS-Pfad |

**Abgrenzung:** Die Tabelle bildet **repräsentative Prozessfamilien** ab,
nicht jede Klasse/Prozessvariante und nicht die gesamte Regressionstest-Suite
des OGS-Quellcodes. Insbesondere sind keine vollständigen validierten
MFront-Materialbenchmark- oder TH2M-Langzeittests enthalten. Für eine
spezifische Prozessklasse kann man weitere Referenz-PRJs aus
`~/ogs-workshop/src/ogs/Tests/Data` ergänzen. Der Build aktiviert
trotzdem **alle** OGS-Prozesse.

Einzeltests durchführen:

```bash
source ~/ogs-workshop/activate.sh
python verify.py --models --only steady_diffusion --only small_deformation \
  --ogs "$OGS_BIN_PATH/ogs" \
  --source ~/ogs-workshop/src/ogs/Tests/Data \
  --output ~/ogs-workshop/results \
  --timeout 90
```

## 4. Fehlerdiagnose

- **`sudo apt-get update` schlägt fehl:** Unterschriebene Paketquellen
  reparieren; nicht mit `--allow-unauthenticated` umgehen.
- **MKL vorhanden, aber `omp_in_parallel` fehlt:** Intel-OpenMP-Laufzeit
  `libiomp5.so` wird benötigt. Die Toolkit-Installation und `activate.sh`
  stellen sie bereit.
- **MFront wird beim CMake-Konfigurieren nicht gefunden:** `--tfel`
  ausführen, dann `--ogs` starten. Prüfen: `mfront --version`.
- **VTK-Compile dauert lange:** Nur bei aktiver CPU-Auslastung und
  neu erzeugten Objekten weiterlaufen lassen; ein externes VTK-Projekt
  kann im oberen Build-Log lange ohne neue Zeilen kompilieren.
- **OGSTools verwendet falsches OGS:** `echo "$OGS_BIN_PATH"` prüfen.
- **ParaView/VS Code lassen sich nicht öffnen:** Für GUI wird eine
  Desktop-Sitzung benötigt; auf reinen SSH-Servern ohne Display ist die
  Installation trotzdem prüfbar, aber keine GUI-Lauftestbestätigung.
- **Keine Python-Pakete im System-Python:** Bitte *nicht* `sudo pip`
  auf Ubuntu 24.04 verwenden. Stattdessen `source .../activate.sh`.

## 5. Nachvollziehbarkeit und offizielle Quellen

- OpenGeoSys: https://www.opengeosys.org/stable/docs/devguide/getting-started/prerequisites/
- OGS-Quellcode: https://gitlab.opengeosys.org/ogs/ogs
- TFEL/MFront: https://thelfer.github.io/tfel/web/install.html
- Intel oneMKL: https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl-download.html
- OGSTools: https://ogstools.opengeosys.org/stable/user-guide/
- ogs6py: https://github.com/joergbuchwald/ogs6py
- VTUinterface: https://github.com/joergbuchwald/VTUinterface
- Gmsh: https://gmsh.info/\n- ParaView: https://www.paraview.org/Download/
- VS Code: https://code.visualstudio.com/docs/setup/linux

Der Installer speichert Quellcode-Commitstände und Installationsprotokolle
lokal. Die exakten `pip`-Versionen lassen sich mit
`~/ogs-workshop/.venv/bin/python -m pip freeze > pip-freeze.txt`
für die Schulung archivieren.

**Die freigegebene Schulungsumgebung gilt erst als geprüft, wenn sowohl
Installations- als auch OGS-/Python-Testbericht erfolgreich sind.**


## Freigabestatus

Die Ubuntu-26.04-Unterstützung ist vorbereitet, aber ein vollständiger Neuaufbau einschließlich GUI-Anwendungen auf 26.04 ist noch nicht end-to-end bestätigt. Die Installation kann systemweite APT-Pakete und Paketquellen ändern. Der öffentliche Quellcode ist ein Schulungsprojekt, keine offizielle OGS-Distribution.

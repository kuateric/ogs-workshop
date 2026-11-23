# Teilnehmerübung – OGS-Baugrube (60 Minuten)

**Modell:** 2D-Diffusion auf einer 65 × 30 m-Domäne. Eine 0,2 m breite ausgesparte Verbauwand reicht von y=30 m bis y=8 m. Links wird das Potential 60, rechts 30 gesetzt. `pressure` ist hier ein mathematisches Potential, kein Wasserdruck in Pa.

| Minute | Gemeinsam durchführen | Checkpoint |
|---|---|---|
| 0–5 | Problem skizzieren, Randwerte und Nullflusswand identifizieren | Richtung des Flusses begründen |
| 5–15 | `geometry/excavation.geo` in Gmsh öffnen; `lc` erläutern, Netz erstellen | Mesh sichtbar |
| 15–25 | `GMSH2OGS`, Bulk- und Randnetze erklären; Conversion-Skripte ausführen | `mesh/excavation.vtu`, `_101.vtu`, `_102.vtu` |
| 25–40 | In `models/excavation.prj` Material, Prozess, `p_bc0`/`p_bc1`, Solver und Ausgabe finden | Teilnehmer erklärt fünf XML-Blöcke |
| 40–45 | `bash scripts/run.sh`; berechnete Felder kontrollieren | OGS-Solver erfolgreich |
| 45–55 | `python scripts/run_variation.py` und Ergebnis in ParaView vergleichen | Werte 60/30 gegen 50/30 |
| 55–60 | Diskussion: Potentialgefälle, Fluss, Modellgrenzen | Eine technische Schlussfolgerung |

## Arbeitsbefehle

Im Ordner `training/ogs-excavation-60min`:

```bash
bash scripts/run.sh
python scripts/check_results.py
python scripts/plot_potential.py
python scripts/run_variation.py
python scripts/check_flux_balance.py
```

### Teilnehmeraufgabe
1. Öffne `models/excavation.prj` und finde den Parameter `p_bc0=60`.
2. Erkläre, warum die Verringerung auf 50 die Potentialdifferenz von 30 auf 20 reduziert.
3. Vergleiche in `results/comparison_bc60_bc50.png` beide Rechnungen mit derselben Farbskala.
4. Zeige in ParaView die jeweilige VTU-Datei für Zeitschritt 1, färbe nach `pressure` und aktiviere Konturlinien. Erkläre, warum die Wandspitze das Feld umlenkt.

**Automatisierte Variante:** `run_variation.py` schreibt eine temporäre Kopie der Projektdatei mit `p_bc0=50` und lässt die Vorlage unverändert.

## Mathematischer Bonus-Check

Für dieses *lineare* stationäre Problem mit gleicher Geometrie, gleichem Diffusionskoeffizienten und rechter Randbedingung 30 gilt theoretisch

```text
u50(x,y) = 30 + (2/3) * (u60(x,y) - 30).
```

Der Test vergleicht die beiden OGS-Felder an sämtlichen Knoten (Toleranz 1e-5).

## Ausweichplan

Wenn auf einem Teilnehmerrechner Netzkonvertierung oder OGS nicht verfügbar sind, zeigt der Dozent die mit dem ThinkStation-CI-Lauf vorab erzeugten VTU-Dateien. Die alte `drainage_excavation.prj` des OGS-Benchmarks ist **nicht** geometrisch identisch mit unserem Schulungsbeispiel.

## Was diese Fallstudie nicht beweist

Keine physikalische Entwässerungsmenge, keine Darcy-Wasserbilanz und keine validierte transient gekoppelte Grundwasserströmung. Die verwendete ThinkStation-OGS-Version ist `g8ffec079`; eine Ausführung mit dem Originalbinary 6.5.9 wurde noch nicht gezeigt.

## Abschluss – 5-Minuten-Flussbilanz

Die Auswertung `results/discrete_flux_balance.csv` enthält die diskreten FEM-Randreaktionen. Für die Referenz sind es links `+10.0450391386` und rechts `-10.0450391386`; bei der Variation links `+6.69669275904` und rechts `-6.69669275904`. Zahlen aus dem nativen [ThinkStation-Test #45153779850](https://github.com/kuateric/engineering-os/actions/runs/45153779850).

Fragen: Warum summieren sich Zu- und Abfluss zu annähernd null? Warum beträgt das Flussverhältnis 2/3? Weshalb dürfen die Zahlen ohne Kalibrierung nicht als m³/s interpretiert werden?

**Wichtig:** Dies ist eine Bilanz über die Dirichlet-Reaktionen aus der assemblierten linearen FEM-Steifigkeit (unter der Annahme `diffusion=1`). Es ist kein punktweiser Beweis verschwindender Flüsse an jeder undurchlässigen Wandkante.

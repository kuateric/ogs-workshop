# Working with OpenGeoSys — NUMO Workshop introduction

Fourteen-slide English Beamer presentation (16:9). This gives the physical and numerical workflow before the nine Jupyter notebooks.

## Files
- \`OGS_Excavation_Introduction.tex\` — editable LaTeX/Beamer sources
- \`generate_assets.py\` — generates diagrams using repository geometry, existing VTU and CSV results; extracts the BGE TEC logo from the original PowerPoint template
- \`OGS_Excavation_Introduction.pdf\` — generated presentation, committed by the PDF build workflow

## Build locally
From this presentation folder:

\`\`\`bash
python3 -m pip install --user numpy matplotlib scipy meshio pillow
python3 generate_assets.py
pdflatex -interaction=nonstopmode -halt-on-error OGS_Excavation_Introduction.tex
pdflatex -interaction=nonstopmode -halt-on-error OGS_Excavation_Introduction.tex
\`\`\`

Requires \`pdflatex\` and a LaTeX Beamer installation. External OGS calculation is **not** required to build the slides because the training repository contains the already computed VTUs.

Scientific basis: \`../geometry/excavation.geo\`, \`../models/excavation.prj\`, \`../results/discrete_flux_balance.csv\` and \`../results/*.vtu\`.
The scalar named \`pressure\` is used here as an abstract potential; integrated reactions are model quantities, not calibrated flow rates. Images generated from the VTUs are real simulation fields. The original BGE TEC PowerPoint is preserved.

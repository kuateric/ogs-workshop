#!/usr/bin/env python3
"""Independent VS Code/terminal executable workflow. No Jupyter, no OGSTools.
Run from anywhere: python run_step.py <1|2|3|4|5|6|7|8|9|all>
"""
from pathlib import Path
import sys, subprocess, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parent

def run(*command):
    print('RUN:', ' '.join(map(str,command)),flush=True)
    subprocess.run([str(x) for x in command],cwd=ROOT,check=True)

def main(step):
    if step == 1:
        source=ROOT/'geometry'/'excavation.geo'
        assert source.exists()
        print(source.read_text())
        run(sys.executable, 'plot_step.py','geometry')
    elif step == 2:
        # Gmsh Python package from the same kernel avoids /usr/local/bin/gmsh wrapper problems
        try:
            import gmsh
        except ImportError as exc:
            raise SystemExit('Install Gmsh into THIS Python: uv pip install gmsh') from exc
        (ROOT/'mesh').mkdir(exist_ok=True)
        gmsh.initialize()
        try:
            gmsh.open(str(ROOT/'geometry'/'excavation.geo'))
            gmsh.option.setNumber('Mesh.MshFileVersion',2.1)
            gmsh.model.mesh.generate(2)
            gmsh.write(str(ROOT/'mesh'/'excavation.msh'))
        finally:
            gmsh.finalize()
        run(sys.executable,'scripts/check_wall_mesh.py','mesh/excavation.msh')
        run(sys.executable,'plot_step.py','mesh')
    elif step == 3:
        run('GMSH2OGS','-i','mesh/excavation.msh','-o','mesh/excavation.vtu','-e','-b')
        run(sys.executable,'scripts/orient_bulk_mesh.py')
        run(sys.executable,'plot_step.py','material')
    elif step == 4:
        run(sys.executable,'scripts/assign_boundary_meshes.py')
        run(sys.executable,'plot_step.py','boundaries')
    elif step == 5:
        tree=ET.parse(ROOT/'models'/'excavation.prj')
        data={p.findtext('name'):p.findtext('value') for p in tree.findall('./parameters/parameter')}
        assert data['p_bc0']=='60' and data['p_bc1']=='30'
        print('OGS Dirichlet parameters:',data)
        run(sys.executable,'plot_step.py','setup')
    elif step == 6:
        (ROOT/'results').mkdir(exist_ok=True)
        run('ogs','-o','results','models/excavation.prj')
        run(sys.executable,'scripts/check_results.py')
        run(sys.executable,'plot_step.py','solution')
    elif step == 7:
        run(sys.executable,'scripts/run_variation.py')
        run(sys.executable,'plot_step.py','comparison')
    elif step == 8:
        run(sys.executable,'plot_step.py','flow')
    elif step == 9:
        run(sys.executable,'scripts/check_results.py')
        run(sys.executable,'scripts/check_flux_balance.py')
        run(sys.executable,'plot_step.py','balance')
    else:
        raise SystemExit('Usage: python run_step.py {1..9|all}')
    print(f'PASS: Step {step} completed')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python run_step.py {1..9|all}')
    if sys.argv[1]=='all':
        for i in range(1,10):main(i)
    else:
        try:step=int(sys.argv[1])
        except ValueError:raise SystemExit('Expected step 1..9 or all')
        main(step)

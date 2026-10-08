from pathlib import Path
import importlib.util,os,sys
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
spec=importlib.util.spec_from_file_location('owned_supervisor',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
m.ENV['PYTHONPATH']=str(ROOT.parent/'r8-ge-footprint-gravity-installed-v1/site')+os.pathsep+str(REPO)
m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_mixed_system_dev.py'),'--input',str(ROOT.parent/'r8-bl5-affine-flexible-v1'),'--output',str(ROOT/'result.json')],'mixed-run',1024**3)

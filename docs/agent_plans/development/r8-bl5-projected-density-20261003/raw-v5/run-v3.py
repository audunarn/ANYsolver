from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('owned_supervisor',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
m.ENV['PYTHONPATH']=str(ROOT.parent/'r8-ge-footprint-gravity-installed-v1/site')
m.supervise([sys.executable,'-u','C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001/scripts/r8_bl5_projected_density_patch_dev.py','--fixed',str(ROOT.parent/'r8-bl5-affine-flexible-fixed-eight-fine-v1'),'--growing',str(ROOT.parent/'r8-bl5-growing-affine-fine-v1'),'--output',str(ROOT/'result-v3.json')],'patch-wrench-v3',1024**3)

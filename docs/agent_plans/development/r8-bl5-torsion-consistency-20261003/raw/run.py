from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('owned_supervisor',OLD)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
m.supervise([sys.executable,'-u','C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001/scripts/r8_bl5_saved_torsion_patch_dev.py','--fixed',str(ROOT.parent/'r8-bl5-affine-flexible-fixed-eight-fine-v1'),'--growing',str(ROOT.parent/'r8-bl5-growing-affine-fine-v1'),'--output',str(ROOT/'result.json')],'patch-run',1024**3)

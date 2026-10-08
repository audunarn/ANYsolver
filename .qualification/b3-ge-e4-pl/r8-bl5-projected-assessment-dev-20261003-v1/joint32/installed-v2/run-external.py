from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
repo=Path("C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
site=root/"site"
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=";".join(map(str,(site,repo,repo/"scripts",repo/"tests")))
m.ENV['PYTHONPATH']=str(root/'external-fixtures')
for name in ('BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):m.ENV[name]='1'
for case in ('fy','mx','mz'):
 m.supervise(['C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',str(root/'external-fixtures/r8_bl5_projected_joint_external_dev.py'),'--site','C:/Python/Python314/Lib/site-packages','--case',case,'--output-dir',str(root/'external'/case)],'external-'+case,1024**3)
